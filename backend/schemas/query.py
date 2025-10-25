from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """
    The incoming request from the user.
    It contains their single natural language query.
    """

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(
        ..., min_length=1, description="The user's natural language query."
    )


class SQLResult(BaseModel):
    """
    A sub-model to hold the structured data from a SQL query.
    """

    model_config = ConfigDict(from_attributes=True)

    columns: List[str] = Field(..., description="List of column names.")
    rows: List[List[Any]] = Field(..., description="List of data rows.")
    generated_query: str = Field(
        ..., description="The exact SQL query that was executed."
    )


class DocumentResult(BaseModel):
    """
    A sub-model to hold a single chunk of unstructured data
    from a document search.
    """

    model_config = ConfigDict(from_attributes=True)

    source_file: str = Field(..., description="The name of the source document.")
    chunk_index: int = Field(
        ..., description="The index of the chunk within the source file."
    )
    content: str = Field(..., description="The text content of the matching chunk.")
    similarity_score: float = Field(
        ..., description="The relevance score from the vector search."
    )


class QueryResponse(BaseModel):
    """
    The final, combined response sent back to the client.
    It flexibly provides SQL results, document results, or both.
    """

    model_config = ConfigDict(from_attributes=True)

    query_type: Literal["sql", "document", "hybrid", "unknown"] = Field(
        ..., description="The type of query that was detected and executed."
    )

    sql_result: SQLResult | None = Field(
        default=None, description="The results from the SQL database (if any)."
    )

    document_results: List[DocumentResult] = Field(
        default=[], description="A list of relevant document chunks (if any)."
    )

    performance_metrics: Dict[str, float] = Field(
        default={},
        description="Server-side performance timing (e.g., {'total_time': 1.23}).",
    )
