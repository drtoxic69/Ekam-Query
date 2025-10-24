from typing import Any, List

from pydantic import BaseModel, ConfigDict


class ConstraintDetail(BaseModel):
    """Describes a table constraint (e.g., UNIQUE)."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    type: str
    columns: List[str]


class IndexDetail(BaseModel):
    """Describes a database index."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    columns: List[str]
    is_unique: bool


class ColumnDetail(BaseModel):
    """Describes a single column in a database table."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    type: str
    is_nullable: bool
    is_primary_key: bool
    is_unique: bool
    foreign_key: str | None = None
    default_value: Any | None = None


class TableDetail(BaseModel):
    """Describes a single table, its columns, and metadata."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    columns: List[ColumnDetail]
    constraints: List[ConstraintDetail]
    indexes: List[IndexDetail]


class SchemaResponse(BaseModel):
    """
    The full API response for a discovered schema.
    This is the top-level object returned by the /api/schema endpoint.
    """

    model_config = ConfigDict(from_attributes=True)

    total_tables: int
    tables: List[TableDetail]
