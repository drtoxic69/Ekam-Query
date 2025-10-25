import asyncio
import logging
import time
from typing import Any, Dict, List, Literal, Tuple, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from transformers import T5ForConditionalGeneration, T5Tokenizer, pipeline

from backend.core.config import settings
from backend.schemas.query import DocumentResult, QueryResponse, SQLResult
from backend.schemas.schema import SchemaResponse
from backend.services.document_processor import EMBEDDING_MODEL, VECTOR_COLLECTION
from backend.services.schema_discovery import SchemaDiscoveryService

logger = logging.getLogger(__name__)

try:
    logger.info("Loading Text-to-SQL model...")

    SQL_MODEL_NAME = "cssupport/t5-small-awesome-text-to-sql"
    SQL_TOKENIZER = T5Tokenizer.from_pretrained(SQL_MODEL_NAME)
    SQL_MODEL = T5ForConditionalGeneration.from_pretrained(SQL_MODEL_NAME)

    logger.info("Text-to-SQL model loaded.")
    logger.info("Loading Query Classification model...")

    CLASSIFIER = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    logger.info("Query Classification model loaded.")

except Exception as e:
    logger.critical(f"Failed to load local ML models: {e}", exc_info=True)
    raise RuntimeError(f"Could not initialize QueryEngineService: {e}")

QUERY_CACHE: Dict[str, Tuple[float, QueryResponse]] = {}
CACHE_TTL = settings.CACHE_TTL_SECONDS
CACHE_MAX_SIZE = settings.CACHE_MAX_SIZE
logger.info(
    f"Global query cache initialized with TTL: {CACHE_TTL} seconds, Max Size: {CACHE_MAX_SIZE}."
)


class QueryEngineService:
    """
    Handles the logic for receiving a natural language query,
    classifying it, and fetching results from SQL or documents.
    Uses a global module-level cache.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize SchemaDiscoveryService without db, as it gets its own connection
        self.schema_service = SchemaDiscoveryService()
        self.vector_collection = VECTOR_COLLECTION
        self.embedding_model = EMBEDDING_MODEL

    async def process_query(self, query: str) -> QueryResponse:
        """Main entry point for processing a user's query with caching."""
        start_time = time.perf_counter()
        current_time = time.time()
        cache_status: Literal["hit", "miss"] = "miss"

        if query in QUERY_CACHE:
            timestamp, cached_response = QUERY_CACHE[query]

            if current_time - timestamp < CACHE_TTL:
                logger.info(f"Cache hit for query: '{query}'")
                cached_response.performance_metrics["total_time_seconds"] = round(
                    time.perf_counter() - start_time, 2
                )
                cached_response.cache_status = "hit"
                return cached_response

            else:
                logger.info(f"Cache expired for query: '{query}'")
                QUERY_CACHE.pop(query, None)
        else:
            logger.info(f"Cache miss for query: '{query}'")

        schema = await self.schema_service.analyze_database()
        schema_prompt = self._create_schema_prompt(schema)

        query_type = await self._classify_query(query)
        logger.info(f"Query classified as: {query_type}")

        sql_result: SQLResult | None = None
        doc_results: List[DocumentResult] = []

        try:
            if query_type == "sql":
                sql_result = await self._execute_sql_query(query, schema_prompt)

            elif query_type == "document":
                doc_results = await self._execute_document_query(query)

            elif query_type == "hybrid":
                sql_task = asyncio.create_task(
                    self._execute_sql_query(query, schema_prompt)
                )
                doc_task = asyncio.create_task(self._execute_document_query(query))
                sql_result, doc_results = await asyncio.gather(sql_task, doc_task)

            else:
                logger.warning("Unknown query type. Defaulting to document search.")
                doc_results = await self._execute_document_query(query)

        except Exception as e:
            logger.error(f"Error during query execution: {e}", exc_info=True)
            raise

        end_time = time.perf_counter()

        response = QueryResponse(
            query_type=query_type,
            sql_result=sql_result,
            document_results=doc_results,
            performance_metrics={"total_time_seconds": round(end_time - start_time, 2)},
            cache_status=cache_status,
        )

        QUERY_CACHE[query] = (current_time, response)
        logger.info(f"Stored result in cache for query: '{query}'")

        if len(QUERY_CACHE) > CACHE_MAX_SIZE:
            try:
                oldest_query = min(QUERY_CACHE, key=lambda k: QUERY_CACHE[k][0])
                del QUERY_CACHE[oldest_query]
                logger.info(
                    f"Cache full ({len(QUERY_CACHE)}/{CACHE_MAX_SIZE}). Removed oldest entry for query: '{oldest_query}'"
                )

            except ValueError:
                pass

        return response

    async def _classify_query(
        self, query: str
    ) -> Literal["sql", "document", "hybrid", "unknown"]:
        """
        Classifies the query using rules first, then falls back to
        a local zero-shot ML model.
        """
        query_lower = query.lower().strip()

        sql_keywords = [
            "list all",
            "show me",
            "select ",
            "how many",
            "average salary",
            "count ",
            "find employees",
            "who reports to",
            "top 5",
        ]

        for keyword in sql_keywords:
            if query_lower.startswith(keyword):
                logger.info(f"Classified as 'sql' based on rule: '{keyword}'")
                return "sql"

        logger.info("No rule matched. Using ML classifier...")
        labels = ["database query", "document search"]

        result = await asyncio.to_thread(CLASSIFIER, query, labels, multi_label=True)

        result_dict = cast(Dict[str, Any], result)
        scores = dict(zip(result_dict["labels"], result_dict["scores"]))

        logger.info(f"Classifier scores for query '{query}': {scores}")

        db_score = scores.get("database query", 0.0)
        doc_score = scores.get("document search", 0.0)

        if db_score > 0.5 and doc_score > 0.5:
            return "hybrid"

        if db_score > 0.5:
            return "sql"

        if doc_score > 0.5:
            return "document"

        return "unknown"

    async def _execute_sql_query(self, query: str, schema_prompt: str) -> SQLResult:
        """Generates and executes a SQL query."""

        prompt = f"Tables:\n{schema_prompt}\n\nQuery: {query}"

        try:
            inputs = SQL_TOKENIZER(
                prompt, return_tensors="pt", max_length=1024, truncation=True
            )

            model_device = next(SQL_MODEL.parameters()).device
            generated_ids = await asyncio.to_thread(
                SQL_MODEL.generate, **inputs.to(model_device), max_length=512
            )
            generated_sql = SQL_TOKENIZER.decode(
                generated_ids[0], skip_special_tokens=True
            ).strip()

        except Exception as e:
            logger.error(f"Error during SQL generation: {e}", exc_info=True)
            return SQLResult(
                columns=["Error"],
                rows=[[f"SQL Generation Error: {e}"]],
                generated_query="Failed",
            )

        logger.info(f"Generated SQL: {generated_sql}")

        if not generated_sql or not generated_sql.upper().strip().startswith("SELECT"):
            logger.warning(f"Generated query was not a valid SELECT: '{generated_sql}'")
            return SQLResult(
                columns=[],
                rows=[],
                generated_query=f"BLOCKED: {generated_sql or 'Empty'}",
            )

        try:
            result = await self.db.execute(text(generated_sql))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]
            return SQLResult(columns=columns, rows=rows, generated_query=generated_sql)

        except Exception as e:
            logger.error(
                f"Error executing generated SQL '{generated_sql}': {e}", exc_info=True
            )
            return SQLResult(
                columns=["Error"],
                rows=[[f"SQL Execution Error: {e}"]],
                generated_query=generated_sql,
            )

    async def _execute_document_query(self, query: str) -> List[DocumentResult]:
        """Performs a vector search on the document collection."""

        try:
            query_embedding = await asyncio.to_thread(
                self.embedding_model.encode, [query]
            )

            results = self.vector_collection.query(
                query_embeddings=query_embedding.tolist(), n_results=5
            )

            docs = []

            if not results or not results.get("ids") or not results["ids"][0]:
                logger.info("No relevant document chunks found.")
                return []

            result_ids = results["ids"][0]
            result_documents_list = results.get("documents")
            result_metadatas_list = results.get("metadatas")
            result_distances_list = results.get("distances")

            if (
                not result_documents_list
                or not result_metadatas_list
                or not result_distances_list
            ):
                logger.error(
                    "ChromaDB results missing documents, metadatas, or distances list."
                )
                return []

            result_documents = result_documents_list[0]
            result_metadatas = result_metadatas_list[0]
            result_distances = result_distances_list[0]

            if not (
                len(result_ids)
                == len(result_documents)
                == len(result_metadatas)
                == len(result_distances)
            ):
                logger.error("ChromaDB result lists have inconsistent lengths.")
                return []

            for i in range(len(result_ids)):
                metadata = result_metadatas[i] or {}
                source_file = str(metadata.get("source_file", "unknown"))
                chunk_index = int(metadata.get("chunk_index", 0))

                docs.append(
                    DocumentResult(
                        source_file=source_file,
                        chunk_index=chunk_index,
                        content=str(result_documents[i]),
                        similarity_score=float(result_distances[i]),
                    )
                )
            return docs

        except Exception as e:
            logger.error(f"Error during document query: {e}", exc_info=True)
            return []

    def _create_schema_prompt(self, schema: SchemaResponse) -> str:
        """Converts your discovered schema into a simple text prompt for the LLM."""
        prompt = ""
        for table in schema.tables:
            prompt += f"Table {table.name}(\n"
            col_strings = [f"  {col.name} ({col.type})" for col in table.columns]
            prompt += ",\n".join(col_strings) + "\n)\n"

        return prompt
