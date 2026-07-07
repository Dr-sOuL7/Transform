"""DOCX writer: persist the (in-place edited) document to a new ``.docx``.

Because transformations mutate live python-docx run objects, exporting is just
a save. Everything the engine never touched is preserved byte-for-byte by
python-docx.
"""

from __future__ import annotations

from .model import Document


def export_docx(document: Document, out_path: str) -> str:
    """Save ``document`` to ``out_path`` and return the path written."""
    if document.docx is None:
        raise ValueError("Document has no underlying docx to export.")
    document.docx.save(out_path)
    return out_path
