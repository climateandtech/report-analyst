#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

# Ensure repo root is on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict, List

from app.core.benchmark.dataset_loader import DatasetLoader
from app.core.benchmark.evaluation_engine import EvaluationEngine
from app.models.benchmark import RetrievalConfig
from report_analyst.core.analyzer import DocumentAnalyzer


def _pdf_from_question_id(reports_dir: Path, question_id: str) -> Path:
    parts = question_id.split("__")
    if len(parts) < 3:
        raise ValueError(f"Unexpected question_id format: {question_id}")
    report_stem = parts[1]

    exact = list(reports_dir.glob(f"{report_stem}.pdf"))
    if exact:
        return exact[0]

    for p in reports_dir.glob("*.pdf"):
        if p.stem.lower() == report_stem.lower():
            return p

    raise FileNotFoundError(f"Could not find PDF for report_stem='{report_stem}' in {reports_dir}")


async def _retrieve_for_question(
    analyzer: DocumentAnalyzer,
    pdf_path: Path,
    question_text: str,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
) -> List[Dict]:
    analyzer.update_parameters(chunk_size=chunk_size, chunk_overlap=chunk_overlap, top_k=top_k)

    chunks = analyzer.cache_manager.get_document_chunks(str(pdf_path), chunk_size, chunk_overlap)
    if not chunks:
        analyzer._create_chunks(str(pdf_path))
        chunks = analyzer.cache_manager.get_document_chunks(str(pdf_path), chunk_size, chunk_overlap)

    analyzer.current_file_path = str(pdf_path)

    retrieved = await analyzer._get_similar_chunks(question_text, chunks, top_k)

    # normalize to string IDs for evaluation
    out = []
    for r in retrieved:
        r2 = dict(r)
        r2["id"] = str(r2.get("id", r2.get("chunk_id", "")))
        out.append(r2)
    return out


async def main_async(args):
    dataset = DatasetLoader().load_dataset(str(args.dataset_yaml))

    analyzer = DocumentAnalyzer()
    retrieval_results: Dict[str, List[Dict]] = {}

    for q in dataset.questions:
        pdf_path = _pdf_from_question_id(args.reports_dir, q.question_id)
        retrieval_results[q.question_id] = await _retrieve_for_question(
            analyzer=analyzer,
            pdf_path=pdf_path,
            question_text=q.question_text,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            top_k=args.top_k,
        )

    engine = EvaluationEngine()
    config = RetrievalConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        top_k=args.top_k,
        use_llm_scoring=False,
        embedding_model="openai",
        similarity_threshold=0.0,
        llm_model=None,
    )

    metrics = engine.evaluate_retrieval(
        dataset=dataset,
        retrieval_results=retrieval_results,
        config=config,
        k_values=args.k_values,
    )

    result_obj = {
        "dataset_id": dataset.dataset_id,
        "retrieval_config": config.model_dump(),
        "metrics": metrics.model_dump(),
        "num_questions": len(dataset.questions),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result_obj, indent=2), encoding="utf-8")

    print("\n=== Benchmark summary ===")
    print(f"Dataset: {dataset.dataset_id}")
    print(f"Questions: {len(dataset.questions)}")
    print(f"MAP: {metrics.mean_average_precision:.4f}")
    print(f"MRR: {metrics.mean_reciprocal_rank:.4f}")
    for k in args.k_values:
        print(
            f"P@{k}: {metrics.precision_at_k.get(k,0.0):.4f} | "
            f"R@{k}: {metrics.recall_at_k.get(k,0.0):.4f} | "
            f"F1@{k}: {metrics.f1_at_k.get(k,0.0):.4f} | "
            f"nDCG@{k}: {metrics.ndcg_at_k.get(k,0.0):.4f}"
        )

    print(f"\nWrote results JSON: {args.out_json}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-yaml", type=Path, required=True)
    p.add_argument("--reports-dir", type=Path, required=True)
    p.add_argument("--chunk-size", type=int, default=500)
    p.add_argument("--chunk-overlap", type=int, default=20)
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--k-values", type=int, nargs="+", default=[1, 3, 5, 10])
    p.add_argument("--out-json", type=Path, required=True)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
