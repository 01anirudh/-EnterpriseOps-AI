"""
Embedding generation using SentenceTransformers (local, no API key needed).
Falls back to a simple hash-based mock if model fails to load.
"""
import logging
from functools import lru_cache
from typing import List, Union

import numpy as np

from backend.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load SentenceTransformer model (cached singleton)."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info(f"✅ Loaded embedding model: {settings.EMBEDDING_MODEL}")
        return model
    except Exception as e:
        logger.warning(f"⚠️  Could not load SentenceTransformer: {e}. Using mock embeddings.")
        return None


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings.
    Returns list of float vectors of dimension EMBEDDING_DIMENSION.
    """
    if not texts:
        return []

    model = get_embedding_model()

    if model is not None:
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    # Mock fallback: reproducible pseudo-random vectors from text hash
    logger.warning("Using mock embeddings (SentenceTransformer not available)")
    result = []
    dim = settings.EMBEDDING_DIMENSION
    for text in texts:
        rng = np.random.RandomState(hash(text) % (2**31))
        vec = rng.randn(dim).astype(np.float32)
        vec = vec / (np.linalg.norm(vec) + 1e-10)
        result.append(vec.tolist())
    return result


def embed_single(text: str) -> List[float]:
    """Embed a single text string."""
    return embed_texts([text])[0]


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """
    Split text into overlapping chunks by character count.
    Tries to split on sentence boundaries when possible.
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = " ".join(text.split())

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to find a sentence boundary (. or \n) to cut on
            boundary = text.rfind(". ", start, end)
            if boundary == -1:
                boundary = text.rfind(" ", start, end)
            if boundary != -1 and boundary > start:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def extract_text_from_file(file_path: str) -> str:
    """
    Extract raw text from a supported file type.
    Supports: PDF, DOCX, XLSX, CSV, TXT
    """
    from pathlib import Path
    path = Path(file_path)
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf":
            return _extract_pdf(file_path)
        elif suffix == ".docx":
            return _extract_docx(file_path)
        elif suffix in (".xlsx", ".xls"):
            return _extract_excel(file_path)
        elif suffix == ".csv":
            return _extract_csv(file_path)
        else:
            # TXT or unknown — read as text
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""


def _extract_pdf(file_path: str) -> str:
    import PyPDF2
    text_parts = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def _extract_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_excel(file_path: str) -> str:
    import pandas as pd
    df = pd.read_excel(file_path, sheet_name=None)
    parts = []
    for sheet_name, sheet_df in df.items():
        parts.append(f"Sheet: {sheet_name}\n{sheet_df.to_string(index=False)}")
    return "\n\n".join(parts)


def _extract_csv(file_path: str) -> str:
    import pandas as pd
    df = pd.read_csv(file_path)
    return df.to_string(index=False)
