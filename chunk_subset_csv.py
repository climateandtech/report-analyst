import argparse
import csv
from pathlib import Path

from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import PyMuPDFReader


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
    chunks_440: list[str],
    chunks_770: list[str],
) -> list[list]:
    """
    Build rows for the CSV.

    Columns:
      0: 250-size chunk text
      1: 440-size chunk text (same index, or empty if missing)
      2: 770-size chunk text (same index, or empty if missing)
      3: bool: 250-size chunk is substring of ANY 440-size chunk
      4: bool: 250-size chunk is substring of ANY 770-size chunk
      5: bool: 440-size chunk is substring of ANY 770-size chunk
    """

    def safe_get(lst: list[str], idx: int) -> str:
        return lst[idx] if idx < len(lst) else ""

    max_len = max(len(chunks_250), len(chunks_440), len(chunks_770))
    rows: list[list] = []

    for i in range(max_len):
        c250 = safe_get(chunks_250, i)
        c440 = safe_get(chunks_440, i)
        c770 = safe_get(chunks_770, i)

        # Subset checks are across ALL chunks of the target size, not just same index
        c250_in_any_440 = bool(c250) and any(c250 in t for t in chunks_440)
        c250_in_any_770 = bool(c250) and any(c250 in t for t in chunks_770)
        c440_in_any_770 = bool(c440) and any(c440 in t for t in chunks_770)

        rows.append(
            [
                c250,
                c440,
                c770,
                c250_in_any_440,
                c250_in_any_770,
                c440_in_any_770,
            ]
        )

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Compare chunks at sizes 250/440/770 and export subset relationships to CSV."
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

    print("Creating chunks (size=440)...")
    chunks_440 = extract_chunks(pdf_path, chunk_size=440, chunk_overlap=overlap)
    print(f"  -> {len(chunks_440)} chunks")

    print("Creating chunks (size=770)...")
    chunks_770 = extract_chunks(pdf_path, chunk_size=770, chunk_overlap=overlap)
    print(f"  -> {len(chunks_770)} chunks")

    # Build CSV rows
    print("Building comparison rows...")
    rows = build_rows(chunks_250, chunks_440, chunks_770)

    # Write CSV
    print(f"Writing CSV to: {out_path}")
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "chunk_250",
                "chunk_440",
                "chunk_770",
                "is_250_subset_of_any_440",
                "is_250_subset_of_any_770",
                "is_440_subset_of_any_770",
            ]
        )
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()
