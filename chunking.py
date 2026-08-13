import re
from typing import List
from src.ingestion import DocumentChunk


class ProcedureDetector:
    # Key trigger phrases signaling synthetic chemistry procedures
    EXPERIMENTAL_PATTERNS = [
        r"(?i)to a solution of",
        r"(?i)was added",
        r"(?i)stirred at \d+\s*°C",
        r"(?i)extracted with",
        r"(?i)purified by silica gel",
        r"(?i)afforded compound",
        r"(?i)yielded"
    ]

    SECTION_EXCLUSIONS = [
        r"(?i)^references",
        r"(?i)^acknowledgments",
        r"(?i)^introduction",
        r"(?i)^computational methods"
    ]

    def is_experimental_chunk(self, text: str) -> bool:
        """Determines if a document chunk contains experimental synthetic procedures."""
        # Check exclusions
        for exc in self.SECTION_EXCLUSIONS:
            if re.search(exc, text[:100]):
                return False

        # Count heuristic matches
        matches = sum(1 for pat in self.EXPERIMENTAL_PATTERNS if re.search(pat, text))
        return matches >= 2

    def extract_procedures(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Filters input document chunks returning only those with procedural chemistry text."""
        return [chunk for chunk in chunks if self.is_experimental_chunk(chunk.text)]
