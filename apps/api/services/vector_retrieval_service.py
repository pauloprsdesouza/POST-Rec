"""pgvector-backed similarity search over stored document embeddings."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.observability.logging import get_logger
from apps.api.settings import get_settings

logger = get_logger("postrec-vector-retrieval")


class VectorRetrievalService:
    """Find semantically similar documents using pgvector cosine distance."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def find_similar_document_ids(
        self,
        db: Session,
        query_embedding: list[float],
        *,
        candidate_ids: list[uuid.UUID] | None = None,
        limit: int = 50,
    ) -> dict[str, float]:
        if not query_embedding:
            return {}

        vector_literal = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"
        params: dict[str, Any] = {"query_vec": vector_literal, "limit": limit}

        if candidate_ids:
            params["candidate_ids"] = [str(doc_id) for doc_id in candidate_ids]
            sql = text(
                """
                SELECT de.document_id::text AS document_id,
                       1 - (de.embedding <=> CAST(:query_vec AS vector)) AS similarity
                FROM document_embedding de
                WHERE de.document_id::text = ANY(:candidate_ids)
                ORDER BY de.embedding <=> CAST(:query_vec AS vector)
                LIMIT :limit
                """
            )
        else:
            sql = text(
                """
                SELECT de.document_id::text AS document_id,
                       1 - (de.embedding <=> CAST(:query_vec AS vector)) AS similarity
                FROM document_embedding de
                ORDER BY de.embedding <=> CAST(:query_vec AS vector)
                LIMIT :limit
                """
            )

        try:
            rows = db.execute(sql, params).mappings().all()
        except Exception as exc:
            logger.warning("vector_retrieval_failed", error=str(exc))
            return {}

        return {row["document_id"]: float(row["similarity"]) for row in rows}


vector_retrieval_service = VectorRetrievalService()
