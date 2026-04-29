from __future__ import annotations

from io import BytesIO

from docx import Document
from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    pass


def extract_text_from_upload(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf_text(content)
    if lower.endswith(".docx"):
        return _extract_docx_text(content)
    raise UnsupportedFileTypeError("Only PDF and DOCX files are supported.")


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n".join(parts).strip()


def _extract_docx_text(content: bytes) -> str:
    doc = Document(BytesIO(content))
    parts: list[str] = []
    for para in doc.paragraphs:
        t = (para.text or "").strip()
        if t:
            parts.append(t)
    return "\n".join(parts).strip()

