import asyncio
import logging
from pathlib import Path
from typing import IO, List

import chromadb
import docx
import pypdf
from chromadb.config import Settings
from fastapi import UploadFile
from sentence_transformers import SentenceTransformer

from backend.core.config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "vectordb"
DB_PATH.mkdir(exist_ok=True)


try:
    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
    EMBEDDING_MODEL = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded successfully.")

    CHROMA_CLIENT = chromadb.Client(
        Settings(
            persist_directory=str(DB_PATH),
            is_persistent=True,
            anonymized_telemetry=False,
        )
    )

    VECTOR_COLLECTION = CHROMA_CLIENT.get_or_create_collection(
        name="employee_documents"
    )
    logger.info(f"ChromaDB collection initialized at: {DB_PATH}")

except Exception as e:
    logger.critical(f"Failed to initialize ML model or vector DB: {e}", exc_info=True)
    raise RuntimeError("Could not initialize DocumentProcessorService")


class DocumentProcessorService:
    """
    Handles the logic for processing, chunking, and embedding
    uploaded documents.
    """

    def __init__(self):
        """
        Initializes the service. We just reference the pre-loaded
        model and collection for speed.
        """
        self.model = EMBEDDING_MODEL
        self.collection = VECTOR_COLLECTION

    async def process_documents(
        self, files: List[UploadFile]
    ) -> tuple[int, int, list[str]]:
        """
        Main function to process a list of uploaded files.
        Returns (num_docs_ingested, num_chunks_created, list_of_doc_ids)
        """
        all_chunks = []
        all_metadatas = []
        all_chunk_ids = []
        files_processed = 0

        for file in files:
            if file.filename is None:
                continue

            logger.info(f"Processing file: {file.filename}")

            try:
                # 1. Extract Text
                text_content = await self._extract_text_from_file(file)
                if not text_content:
                    logger.warning(f"Skipping empty file: {file.filename}")
                    continue

                # 2. Dynamic Chunking
                chunks = self._dynamic_chunking(text_content, file.content_type)
                if not chunks:
                    logger.warning(f"No text chunks extracted from {file.filename}")
                    continue

                # 3. Prepare metadata and IDs for this file's chunks
                chunk_ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
                metadatas = [
                    {"source_file": file.filename, "chunk_index": i}
                    for i in range(len(chunks))
                ]

                # 4. Add to our master lists
                all_chunks.extend(chunks)
                all_metadatas.extend(metadatas)
                all_chunk_ids.extend(chunk_ids)
                files_processed += 1

            except Exception as e:
                logger.error(
                    f"Failed to process file {file.filename}: {e}", exc_info=True
                )

        # 5. Generate & Store Embeddings (if any files were successful)
        if all_chunks:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")

            embeddings = await asyncio.to_thread(
                self.model.encode,
                all_chunks,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                show_progress_bar=False,
            )

            # 6. Store in ChromaDB in a single batch
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_chunk_ids,
            )
            logger.info(f"Successfully added {len(all_chunks)} chunks to vector store.")

        return files_processed, len(all_chunks), all_chunk_ids

    async def _extract_text_from_file(self, file: UploadFile) -> str:
        """Extracts raw text from an uploaded file."""
        file_content = await file.read()
        file_like_object = self._bytes_to_file_like(file_content)

        text = ""
        try:
            if file.content_type == "application/pdf":
                reader = pypdf.PdfReader(file_like_object)
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"

            elif file.content_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ]:
                doc = docx.Document(file_like_object)
                for para in doc.paragraphs:
                    text += para.text + "\n"

            elif file.content_type == "text/plain":
                text = file_content.decode("utf-8")

            else:
                logger.warning(
                    f"Unsupported file type: {file.content_type} "
                    f"for file {file.filename}. Trying plain text."
                )
                text = file_content.decode("utf-8", errors="ignore")

        except Exception as e:
            logger.error(
                f"Failed to extract text from {file.filename}: {e}", exc_info=True
            )
            return ""

        finally:
            file_like_object.close()

        return text

    def _dynamic_chunking(self, content: str, content_type: str | None) -> List[str]:
        """
        Intelligently chunks text based on document structure.
        """
        logger.debug(f"Chunking document of type {content_type}")

        chunks = content.split(
            "\n\n"
        )  # Add two new lines for 'better' chunking process

        final_chunks = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            final_chunks.append(chunk)

        return final_chunks

    def _bytes_to_file_like(self, content: bytes) -> IO[bytes]:
        """Utility to convert bytes to a file-like object for pypdf/docx."""
        from io import BytesIO

        return BytesIO(content)
