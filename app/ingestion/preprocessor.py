"""Document preprocessing: normalization, noise removal, structure preservation."""

import re
from typing import List

from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)

# Common PDF artifacts in EV manuals
_HEADER_FOOTER_PATTERNS = [
    r"^Page \d+ of \d+\s*$",
    r"^XYZ EV Corp.*$",
    r"^CONFIDENTIAL.*$",
    r"^\d+\s*$",
]


class DocumentPreprocessor:
    """Clean and normalize EV troubleshooting documents before chunking."""

    def __init__(self):
        self._noise_regex = re.compile("|".join(_HEADER_FOOTER_PATTERNS), re.MULTILINE | re.IGNORECASE)

    def preprocess(self, documents: List[Document]) -> List[Document]:
        cleaned: List[Document] = []
        for doc in documents:
            text = self._clean_text(doc.page_content)
            if len(text.strip()) < 30:
                continue
            cleaned.append(
                Document(page_content=text, metadata=dict(doc.metadata))
            )
        logger.info("preprocessing_complete", input_docs=len(documents), output_docs=len(cleaned))
        return cleaned

    def _clean_text(self, text: str) -> str:
        text = text.replace("\x00", " ")
        text = self._noise_regex.sub("", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" ?\n ?", "\n", text)
        return text.strip()
