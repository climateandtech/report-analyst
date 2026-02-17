import argparse
import csv
from pathlib import Path

from llama_index.readers.file import PyMuPDFReader
from llama_index.core.node_parser import SentenceSplitter


def extract_chunks(pdf_path: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Reproduce the analyzer's chunking logic using SentenceSplitter, but skip embeddings.
    Returns a list of chunk texts.
    """
    reader = PyMuPDFReader()
    docs = reader.load(file_path=pdf_path)

    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[str] = []

    for doc in docs:
        nodes = splitter.split_text(doc.text)
        chunks.extend(nodes)

    return chunks


def build_rows(
    chunks_250: list[str],
    chunks_500: list[str],
    chunks_1000: list[str],
) -> list[list]:
    """
    Build rows for the CSV.

    Columns:
      0: 250-size chunk text
      1: 500-size chunk text (same index, or empty if missing)
      2: 1000-size chunk text (same index, or empty if missing)
      3: bool: 250-size chunk is substring of ANY 500-size chunk
      4: bool: 250-size chunk is substring of ANY 1000-size chunk
      5: bool: 500-size chunk is substring of ANY 1000-size chunk
    """
    def safe_get(lst: list[str], idx: int) -> str:
        return lst[idx] if idx < len(lst) else ""

    max_len = max(len(chunks_250), len(chunks_500), len(chunks_1000))
    rows: list[list] = []

    for i in range(max_len):
        c250 = safe_get(chunks_250, i)
        c500 = safe_get(chunks_500, i)
        c1000 = safe_get(chunks_1000, i)

        # Subset checks are across ALL chunks of the target size, not just same index
        c250_in_any_500 = bool(c250) and any(c250 in t for t in chunks_500)
        c250_in_any_1000 = bool(c250) and any(c250 in t for t in chunks_1000)
        c500_in_any_1000 = bool(c500) and any(c500 in t for t in chunks_1000)

        rows.append([
            c250,
            c500,
            c1000,
            c250_in_any_500,
            c250_in_any_1000,
            c500_in_any_1000,
        ])

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Compare chunks at sizes 250/500/1000 and export subset relationships to CSV."
    )
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file to analyze")
    parser.add_argument(
        "--overlap",
        type=int,
        default=20,
        help="Chunk overlap to use for all chunk sizes (default: 20)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="chunk_comparison.csv",
        help="Output CSV file path (default: chunk_comparison.csv)",
    )
    args = parser.parse_args()

    pdf_path = str(Path(args.pdf_path).resolve())
    overlap = args.overlap
    out_path = Path(args.output).resolve()

    print(f"Reading PDF: {pdf_path}")
    print(f"Using chunk_overlap={overlap}")

    # Generate chunks for each size
    print("Creating chunks (size=250)...")
    chunks_250 = extract_chunks(pdf_path, chunk_size=250, chunk_overlap=overlap)
    print(f"  -> {len(chunks_250)} chunks")

    print("Creating chunks (size=500)...")
    chunks_500 = extract_chunks(pdf_path, chunk_size=500, chunk_overlap=overlap)
    print(f"  -> {len(chunks_500)} chunks")

    print("Creating chunks (size=1000)...")
    chunks_1000 = extract_chunks(pdf_path, chunk_size=1000, chunk_overlap=overlap)
    print(f"  -> {len(chunks_1000)} chunks")

    # Build CSV rows
    print("Building comparison rows...")
    rows = build_rows(chunks_250, chunks_500, chunks_1000)

    # Write CSV
    print(f"Writing CSV to: {out_path}")
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "chunk_250",
            "chunk_500",
            "chunk_1000",
            "is_250_subset_of_any_500",
            "is_250_subset_of_any_1000",
            "is_500_subset_of_any_1000",
        ])
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()