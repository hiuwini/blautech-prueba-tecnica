from __future__ import annotations

from fastapi import Request

from app.domain.documents.service import DocumentService


def get_document_service(request: Request) -> DocumentService:
    return request.app.state.document_service
