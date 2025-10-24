import logging
from typing import Any, Dict, List, Set

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession

from backend.schemas.schema import (
    ColumnDetail,
    ConstraintDetail,
    IndexDetail,
    SchemaResponse,
    TableDetail,
)

logger = logging.getLogger(__name__)


class SchemaDiscoveryService:
    """
    Handles the logic for dynamically discovering the database schema.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the service with the current database session.
        """
        self.db = db

    def _get_schema_details_sync(
        self, sync_session: SyncSession
    ) -> List[Dict[str, Any]]:
        """
        Synchronous helper function to perform all database inspection.
        This function is designed to be run inside `db.run_sync()`.

        Args:
            sync_session: A synchronous SQLAlchemy Session object
                          provided by `run_sync`.

        Returns:
            A list of dictionaries, each containing the raw schema
            details for one table.
        """
        logger.debug("Running synchronous schema inspection...")

        with sync_session.connection() as connection:
            inspector = inspect(connection)
            table_names = inspector.get_table_names()
            all_tables_data = []

            for table_name in table_names:
                all_tables_data.append(
                    {
                        "name": table_name,
                        "columns": inspector.get_columns(table_name),
                        "pk_constraint": inspector.get_pk_constraint(table_name),
                        "fks": inspector.get_foreign_keys(table_name),
                        "constraints": inspector.get_unique_constraints(table_name),
                        "indexes": inspector.get_indexes(table_name),
                    }
                )

        logger.debug(f"Sync inspection found {len(all_tables_data)} tables.")

        return all_tables_data

    async def analyze_database(self) -> SchemaResponse:
        """
        Analyzes the database schema in an async-safe way.
        """
        logger.info("Starting database schema analysis...")

        try:
            all_tables_data = await self.db.run_sync(self._get_schema_details_sync)

            logger.info(f"Successfully discovered {len(all_tables_data)} tables.")

            discovered_tables: List[TableDetail] = []

            for table_data in all_tables_data:
                table_name = table_data["name"]
                logger.debug(f"Parsing schema for table: {table_name}")

                pk_columns: Set[str] = set(
                    table_data["pk_constraint"].get("constrained_columns", [])
                )

                table_columns: List[ColumnDetail] = []
                for col in table_data["columns"]:
                    foreign_key_to = self._find_foreign_key(
                        col["name"], table_data["fks"]
                    )

                    table_columns.append(
                        ColumnDetail(
                            name=col["name"],
                            type=str(col["type"]),
                            is_nullable=col["nullable"],
                            is_primary_key=col["name"] in pk_columns,
                            is_unique=col.get("unique", False),
                            foreign_key=foreign_key_to,
                            default_value=col.get("default"),
                        )
                    )

                table_constraints = [
                    ConstraintDetail(
                        name=c["name"], type="UNIQUE", columns=c["column_names"]
                    )
                    for c in table_data["constraints"]
                ]

                table_indexes = [
                    IndexDetail(
                        name=idx["name"],
                        columns=idx["column_names"],
                        is_unique=idx["unique"],
                    )
                    for idx in table_data["indexes"]
                ]

                discovered_tables.append(
                    TableDetail(
                        name=table_name,
                        columns=table_columns,
                        constraints=table_constraints,
                        indexes=table_indexes,
                    )
                )

            return SchemaResponse(
                total_tables=len(discovered_tables), tables=discovered_tables
            )

        except SQLAlchemyError as e:
            logger.error(f"Error during schema discovery: {e}", exc_info=True)
            raise

    def _find_foreign_key(self, col_name: str, fks: List[Dict[str, Any]]) -> str | None:
        """Helper utility to find the FK reference for a given column name."""
        for fk in fks:
            if col_name in fk["constrained_columns"]:
                return f"{fk['referred_table']}.{fk['referred_columns'][0]}"

        return None
