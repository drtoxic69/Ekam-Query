import logging
from functools import lru_cache
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.schemas.ingestion import DocumentIngestResponse
from backend.services.document_processor import DocumentProcessorService

logger = logging.getLogger(__name__)
router = APIRouter()


@lru_cache(None)
def get_doc_processor_service() -> DocumentProcessorService:
    """
    Dependency to get a singleton instance of the DocumentProcessorService.
    This ensures the ML model is loaded only once.
    """
    logger.info("Initializing DocumentProcessorService singleton...")
    return DocumentProcessorService()


@router.post(
    "/ingest/documents",
    response_model=DocumentIngestResponse,
    summary="Ingest and Process Documents",
    description="Upload one or more documents (PDF, DOCX, TXT) to be "
    "processed, chunked, embedded, and stored for querying.",
    tags=["Ingestion"],
)
async def ingest_documents(
    files: List[UploadFile] = File(..., description="List of documents to upload."),
    doc_processor: DocumentProcessorService = Depends(get_doc_processor_service),
):
    """
    Endpoint to upload and process multiple documents.

    It handles:
    - Receiving a list of files.
    - Passing them to the DocumentProcessorService.
    - Returning a summary of the ingestion.
    """
    if not files:
        logger.warning("Ingest documents called with no files.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were uploaded. Please select files to ingest.",
        )

    logger.info(f"Received {len(files)} files for ingestion.")

    try:
        count, chunks, ids = await doc_processor.process_documents(files)

        logger.info(f"Successfully ingested {count} documents as {chunks} chunks.")

        return DocumentIngestResponse(
            total_documents_ingested=count,
            total_chunks_created=chunks,
            document_ids=ids,
            message="Documents ingested successfully.",
        )

    except Exception as e:
        logger.error(f"Failed to ingest documents: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during document processing: {e}",
        )
