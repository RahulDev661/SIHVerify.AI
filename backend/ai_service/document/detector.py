"""
Module 2 — Document Validation.

STATUS: NOT YET IMPLEMENTED.

This module is expected to check that the uploaded image is a
genuine, well-formed identity document before OCR/face pipelines run
on it — e.g. detecting the document boundary, confirming aspect
ratio / layout matches a known passport template, checking print
quality, and flagging obvious non-document images.

The function signature and return shape below are the contract the
FastAPI layer (`app/routers/passport.py`) already calls, so once this
is implemented no router changes should be needed — only this file.
"""

from typing import TypedDict


class DocumentValidationResult(TypedDict):
    valid: bool
    documentType: str | None
    confidence: float
    errors: list[str]


def validate_document(image_path: str) -> DocumentValidationResult:
    """
    Validate that `image_path` contains a genuine, correctly-framed
    identity document.

    TODO:
        - detect document edges / boundary
        - classify document type (passport / national ID / etc.)
        - confirm aspect ratio and layout match the expected template
        - flag blurry, cropped, or non-document images

    Currently a passthrough stub: always reports the document as
    valid with zero confidence, so downstream code can be wired up
    and tested before this module is implemented.
    """

    return DocumentValidationResult(
        valid=True,
        documentType=None,
        confidence=0.0,
        errors=["validate_document() is not implemented yet"],
    )
