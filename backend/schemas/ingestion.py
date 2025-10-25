from typing import List

from pydantic import BaseModel, ConfigDict


class DocumentIngestResponse(BaseModel):
    """
    Defines the simple, synchronous API response for when
    document ingestion is complete.
    """

    model_config = ConfigDict(from_attributes=True)

    total_documents_ingested: int
    total_chunks_created: int
    document_ids: List[str]
    message: str
