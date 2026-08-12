import re
from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
import fitz  # PyMuPDF
from pydantic import BaseModel


class DocumentChunk(BaseModel):
    document_id: str
    file_path: str
    page_number: int
    text: str
    char_start: int
    char_end: int


class PDFIngestor:
    def __init__(self, base_directory: Path):
        self.base_directory = Path(base_directory)
        if not self.base_directory.exists():
            raise FileNotFoundError(f"Source directory does not exist: {self.base_directory}")

    def discover_pdf_files(self) -> List[Path]:
        """Recursively discover PDF files across the materials directory."""
        return list(self.base_directory.rglob("*.pdf"))

    def extract_text_with_provenance(self, pdf_path: Path) -> List[DocumentChunk]:
        """Extract text page by page preserving character spans and document context."""
        chunks: List[DocumentChunk] = []
        doc_id = pdf_path.stem

        try:
            doc = fitz.open(str(pdf_path))
            global_offset = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")

                # Basic cleaning without destroying chemical strings
                page_text_clean = self._clean_raw_text(page_text)
                text_len = len(page_text_clean)

                chunk = DocumentChunk(
                    document_id=doc_id,
                    file_path=str(pdf_path),
                    page_number=page_num + 1,
                    text=page_text_clean,
                    char_start=global_offset,
                    char_end=global_offset + text_len
                )
                chunks.append(chunk)
                global_offset += text_len + 1

            doc.close()
        except Exception as e:
            print(f"[ERROR] Failed to ingest {pdf_path}: {str(e)}")

        return chunks

    @staticmethod
    def _clean_raw_text(text: str) -> str:
        """Removes illegal non-printable ASCII characters while retaining chemical symbols."""
        # Replace hyphens broken by line ends
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        # Normalize double spaces
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()