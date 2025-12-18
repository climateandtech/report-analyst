#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

# Ensure repo root is on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))



import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yaml
from rapidfuzz import process, fuzz

from report_analyst.core.analyzer import DocumentAnalyzer


def _norm_report_name(x: str) -> str:
    x = str(x).strip()
    x = x.replace("\\", "/").split("/")[-1]
    return x


def _find_pdf_for_report(reports_dir: Path, report_value: str) -> Path:
    rv = _norm_report_name(report_value)

    direct = reports_dir / rv
    if direct.exists():
        return direct

    if not rv.lower().endswith(".pdf"):
        cand = reports_dir / f"{rv}.pdf"
        if cand.exists():
            return cand

    pdfs = list(reports_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found in {reports_dir}")

    choices = [p.name for p in pdfs]
    best, score, _ = process.extractOne(rv, choices, scorer=fuzz.WRatio)
    if score < 70:
        raise FileNotFoundError(
            f"Could not map report '{report_value}' to a PDF in {reports_dir} "
            f"(best='{best}', score={score})"
        )
    return reports_dir / best


def _ensure_chunks(analyzer: DocumentAnalyzer, pdf_path: Path, chunk_size: int, chunk_overlap: int) -> List[Dict]:
    analyzer.update_parameters(chunk_size=chunk_size, chunk_overlap=chunk_overlap, top_k=analyzer.chunk_params.get("top_k", 5))

    chunks = analyzer.cache_manager.get_document_chunks(
        file_path=str(pdf_path),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if chunks:
        return chunks

    analyzer._create_chunks(str(pdf_path))

    chunks = analyzer.cache_manager.get_document_chunks(
        file_path=str(pdf_path),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if not chunks:
        raise RuntimeError(f"Chunk creation failed for {pdf_path}")
    return chunks


def _map_paragraph_to_chunk(paragraph: str, chunk_texts: List[str], chunk_ids: List[int], min_match: int) -> Tuple[int, int]:
    paragraph = str(paragraph).strip()
    if not paragraph:
        return -1, 0

    best = process.extractOne(paragraph, chunk_texts, scorer=fuzz.token_set_ratio)
    if best is None:
        return -1, 0

    _, score, idx = best
    if score < min_match:
        return -1, int(score)
    return int(chunk_ids[idx]), int(score)


def build_benchmark_yaml(
    reportlevel_csv: Path,
    reports_dir: Path,
    out_yaml: Path,
    chunk_size: int,
    chunk_overlap: int,
    relevance_threshold: int,
    min_match: int,
    core_questions_only: bool,
) -> None:
    df = pd.read_csv(reportlevel_csv)

    required = {"paragraph", "report", "question", "relevance"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"ReportLevel CSV missing columns: {sorted(missing)}")

    if core_questions_only and "core_16_question" in df.columns:
        df = df[df["core_16_question"] == 1]

    df = df[df["relevance"].fillna(0).astype(int) >= relevance_threshold].copy()

    analyzer = DocumentAnalyzer()

    questions_out = []
    unmatched = 0

    for (report_val, question_text), g in df.groupby(["report", "question"], dropna=False):
        pdf_path = _find_pdf_for_report(reports_dir, report_val)
        chunks = _ensure_chunks(analyzer, pdf_path, chunk_size, chunk_overlap)

        chunk_ids = [c["id"] for c in chunks]
        chunk_texts = [c["text"] for c in chunks]

        # Encode report routing into question_id
        report_stem = pdf_path.stem.replace(" ", "_")
        qhash = hashlib.sha1(f"{pdf_path.name}|{question_text}".encode("utf-8")).hexdigest()[:12]
        question_id = f"clim__{report_stem}__{qhash}"

        gt_chunks = []
        for _, row in g.iterrows():
            para = row["paragraph"]
            rel = int(row["relevance"])

            chunk_id, score = _map_paragraph_to_chunk(para, chunk_texts, chunk_ids, min_match=min_match)
            if chunk_id == -1:
                unmatched += 1
                continue

            rel_norm = max(0.0, min(1.0, rel / 3.0))
            is_evidence = rel >= 2

            gt_chunks.append(
                {
                    "chunk_id": str(chunk_id),  # must match retrieval result ids
                    "relevance_score": float(rel_norm),
                    "is_evidence": bool(is_evidence),
                    "annotation_notes": f"mapped_from=ClimRetrieve_ReportLevel; match_score={score}; report={pdf_path.name}",
                }
            )

        if gt_chunks:
            questions_out.append(
                {
                    "question_id": question_id,
                    "question_text": str(question_text),
                    "ground_truth_chunks": gt_chunks,
                }
            )

    out_yaml.parent.mkdir(parents=True, exist_ok=True)

    dataset = {
        "dataset_id": f"climretrieve_reportlevel_cs{chunk_size}_ov{chunk_overlap}_rel{relevance_threshold}",
        "name": "ClimRetrieve Report-Level (converted to Report Analyst chunks)",
        "description": (
            "Converted from ClimRetrieve Report-Level dataset into Report Analyst benchmark format. "
            "chunk_id values are Report Analyst sqlite document_chunks.id for the given chunk params."
        ),
        "version": "1.0",
        "question_set": "climretrieve",
        "created_at": "",
        "questions": questions_out,
    }

    with open(out_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(dataset, f, sort_keys=False, allow_unicode=True)

    mapped = len(df) - unmatched
    print(f"Wrote dataset YAML: {out_yaml}")
    print(f"Mapping success: {mapped}/{len(df)} rows mapped ({(mapped/max(1,len(df))*100):.1f}%)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reportlevel-csv", type=Path, required=True)
    p.add_argument("--reports-dir", type=Path, required=True)
    p.add_argument("--out-yaml", type=Path, required=True)
    p.add_argument("--chunk-size", type=int, default=500)
    p.add_argument("--chunk-overlap", type=int, default=20)
    p.add_argument("--relevance-threshold", type=int, default=1)
    p.add_argument("--min-match", type=int, default=80)
    p.add_argument("--core-questions-only", action="store_true")
    args = p.parse_args()

    build_benchmark_yaml(
        reportlevel_csv=args.reportlevel_csv,
        reports_dir=args.reports_dir,
        out_yaml=args.out_yaml,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        relevance_threshold=args.relevance_threshold,
        min_match=args.min_match,
        core_questions_only=args.core_questions_only,
    )


if __name__ == "__main__":
    main()
