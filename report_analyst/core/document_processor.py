import shutil
import uuid
from pathlib import Path
from typing import Optional, Union

import fitz  # PyMuPDF
from fastapi import UploadFile

from report_analyst.models.requests import DocumentMetadata


class DocumentProcessor:
    def __init__(self, input_dir: str = "data/input", output_dir: str = "data/output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def process_upload(self, file_path: Union[str, Path]) -> dict:
        """Process a document from a file path and return metadata"""
        try:
            document_id = str(uuid.uuid4())
            source_path = Path(file_path)
            safe_filename = source_path.name
            dest_path = self.input_dir / f"{document_id}_{safe_filename}"

            print(f"Processing upload: {safe_filename}")
            print(f"Destination path: {dest_path}")

            # Ensure parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(str(source_path), str(dest_path))

            # Verify file was copied
            if not dest_path.exists():
                raise ValueError("File was not created")

            file_size = dest_path.stat().st_size
            print(f"Copied file size: {file_size} bytes")

            if file_size == 0:
                raise ValueError("File was copied but is empty")

            # Verify we can open it with PyMuPDF
            try:
                print(f"Attempting to open with PyMuPDF: {dest_path}")
                doc = fitz.open(str(dest_path))
                page_count = doc.page_count
                print(f"Successfully opened PDF with {page_count} pages")
                doc.close()
            except Exception as e:
                print(f"Failed to verify PDF: {str(e)}")
                if dest_path.exists():
                    dest_path.unlink()
                raise ValueError(f"Invalid PDF file: {str(e)}")

            # Extract metadata
            metadata = await self._extract_metadata(dest_path, safe_filename)
            return {"document_id": document_id, "metadata": metadata}
        except Exception as e:
            print(f"Error processing upload: {str(e)}")
            if "dest_path" in locals() and dest_path.exists():
                dest_path.unlink()  # Clean up on error
            raise

    async def _extract_metadata(
        self, file_path: Path, original_filename: str
    ) -> DocumentMetadata:
        """Extract metadata from the document using PyMuPDF"""
        try:
            file_size = file_path.stat().st_size
            file_type = file_path.suffix.lower()[1:]  # Remove the dot

            metadata = {
                "file_type": file_type,
                "file_size": file_size,
                "title": None,
                "author": None,
                "date": None,
                "num_pages": None,
            }

            # Extract PDF metadata using PyMuPDF
            if file_type == "pdf":
                doc = fitz.open(file_path)
                metadata["num_pages"] = doc.page_count
                if doc.metadata:
                    metadata["title"] = doc.metadata.get("title")
                    metadata["author"] = doc.metadata.get("author")
                    metadata["date"] = doc.metadata.get("creationDate")
                doc.close()

            return DocumentMetadata(**metadata)
        except Exception as e:
            print(f"Error in metadata extraction: {e}")
            return DocumentMetadata(
                file_type="unknown",
                file_size=0,
                title=None,
                author=None,
                date=None,
                num_pages=None,
            )

    async def get_document_path(self, document_id: str) -> Optional[Path]:
        """Get the path of a processed document"""
        for file_path in self.input_dir.glob(f"{document_id}_*"):
            return file_path
        return None

    async def cleanup_document(self, document_id: str) -> bool:
        """Clean up processed document files"""
        document_path = await self.get_document_path(document_id)
        if document_path and document_path.exists():
            document_path.unlink()
            return True
        return False
