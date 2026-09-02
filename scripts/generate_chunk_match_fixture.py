#!/usr/bin/env python3
"""Generate a real-world ClimRetrieve chunk-matching fixture with OpenAI embeddings."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import PyMuPDFReader

from report_analyst.core.benchmark.library_eval import normalize_climretrieve_columns

REPOSITORY = "tobischimanski/ClimRetrieve"
REPORT = "CT REIT 2022 ESG Report.pdf"
QUESTION = "Does the company have any engagements with industry peers in relation to climate change?"
LABELS_URL = (
    f"https://raw.githubusercontent.com/{REPOSITORY}/main/"
    "Expert-Annotated%20Relevant%20Sources%20Dataset/ClimRetrieve_base.xlsx"
)
REPORT_URL = f"https://raw.githubusercontent.com/{REPOSITORY}/main/Reports/{quote(REPORT)}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("notebooks/data"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/fixtures/ct_reit_chunk_matching.json"),
    )
    parser.add_argument("--model", default=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"))
    parser.add_argument("--top-candidates", type=int, default=10)
    return parser.parse_args()


def download(url: str, path: Path) -> Path:
    if path.exists() and path.stat().st_size:
        return path
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ground_truth_record(labels_path: Path) -> dict[str, object]:
    labels = normalize_climretrieve_columns(pd.read_excel(labels_path))
    rows = labels[(labels["document"] == REPORT) & (labels["question"] == QUESTION)]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one ground-truth chunk, found {len(rows)}")
    row = rows.iloc[0]
    return {
        "text": str(row["relevant"]).strip(),
        "context": str(row["Context"]).strip(),
        "page": int(row["Page"]),
        "source_from": str(row["Source From"]),
        "answer": str(row["answer"]).strip(),
        "relevance_score": float(row["relevance_score"]),
        "unsure_flag": str(row["Unsure Flag"]),
        "addressed_directly": str(row["Addressed Directly"]),
    }


def chunk_report(report_path: Path, chunk_size: int, chunk_overlap: int) -> list[dict[str, object]]:
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[dict[str, object]] = []
    for page_index, document in enumerate(PyMuPDFReader().load(file_path=report_path), start=1):
        for text in splitter.split_text(document.text):
            clean_text = " ".join(text.split())
            if clean_text:
                chunks.append(
                    {
                        "document_chunk_index": len(chunks),
                        "page": page_index,
                        "text": clean_text,
                    }
                )
    return chunks


def cosine_scores(embeddings: np.ndarray, target: np.ndarray) -> np.ndarray:
    embedding_norms = np.linalg.norm(embeddings, axis=1)
    target_norm = np.linalg.norm(target)
    return embeddings @ target / (embedding_norms * target_norm)


def select_candidates(
    chunks: list[dict[str, object]],
    embeddings: np.ndarray,
    question_embedding: np.ndarray,
    ground_truth_embedding: np.ndarray,
    limit: int,
) -> list[dict[str, object]]:
    question_scores = cosine_scores(embeddings, question_embedding)
    ground_truth_scores = cosine_scores(embeddings, ground_truth_embedding)
    selected = set(np.argsort(question_scores)[-limit:].tolist())
    selected.update(np.argsort(ground_truth_scores)[-limit:].tolist())
    selected.update(index + offset for index in tuple(selected) for offset in (-1, 1))
    selected = {index for index in selected if 0 <= index < len(chunks)}
    rows = []
    for index in sorted(selected):
        rows.append(
            {
                **chunks[index],
                "question_similarity": round(float(question_scores[index]), 8),
                "ground_truth_similarity": round(float(ground_truth_scores[index]), 8),
            }
        )
    return rows


def build_fixture(args: argparse.Namespace) -> dict[str, object]:
    load_dotenv(dotenv_path=Path(".env"))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required to generate this fixture")

    labels_path = download(LABELS_URL, args.data_dir / "ClimRetrieve_base.xlsx")
    report_path = download(REPORT_URL, args.data_dir / "reports" / REPORT)
    ground_truth = ground_truth_record(labels_path)
    relevant_text = str(ground_truth["text"])
    embedder = OpenAIEmbedding(api_key=api_key, model_name=args.model, embed_batch_size=100)
    target_embeddings = embedder.get_text_embedding_batch([QUESTION, relevant_text])
    question_embedding = np.asarray(target_embeddings[0], dtype=np.float32)
    ground_truth_embedding = np.asarray(target_embeddings[1], dtype=np.float32)

    chunk_sets: dict[str, list[dict[str, object]]] = {}
    for chunk_size in (200, 400):
        chunks = chunk_report(report_path, chunk_size, chunk_overlap=20)
        embeddings = np.asarray(
            embedder.get_text_embedding_batch([str(chunk["text"]) for chunk in chunks]),
            dtype=np.float32,
        )
        chunk_sets[str(chunk_size)] = select_candidates(
            chunks,
            embeddings,
            question_embedding,
            ground_truth_embedding,
            args.top_candidates,
        )

    return {
        "fixture_version": 1,
        "source": {
            "repository": REPOSITORY,
            "report": REPORT,
            "report_sha256": sha256(report_path),
            "labels_sha256": sha256(labels_path),
        },
        "question": QUESTION,
        "ground_truth": ground_truth,
        "generation": {
            "embedding_model": args.model,
            "chunk_sizes": [200, 400],
            "chunk_overlap": 20,
            "stored_vectors": False,
        },
        "chunks": chunk_sets,
    }


def main() -> None:
    args = parse_args()
    fixture = build_fixture(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
