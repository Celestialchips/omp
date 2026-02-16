"""SQLite storage backend for OMP extraction results."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from omp.models import (
    ExtractionResult,
    FunctionSignature,
    ClassDefinition,
    ImportStatement,
    Parameter,
)
from omp.storage.base import BaseStorage


class SQLiteStorage(BaseStorage):
    """SQLite-backed storage for ExtractionResults."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        """Create or open the SQLite database and initialize schema."""
        self._db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self) -> None:
        """Establish connection to SQLite and enable WAL mode."""
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.row_factory = sqlite3.Row

    def _create_tables(self) -> None:
        """Create schema: extractions table and indexes."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_id TEXT UNIQUE,
                file TEXT UNIQUE NOT NULL,
                language TEXT,
                file_hash TEXT,
                timestamp TEXT,
                data TEXT
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_extractions_file ON extractions(file)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_extractions_observation_id "
            "ON extractions(observation_id)"
        )
        self._conn.commit()

    def save(self, result: ExtractionResult) -> None:
        """Persist an ExtractionResult, replacing any existing extraction for same file."""
        data_json = json.dumps(result.to_dict())
        self._conn.execute(
            """
            INSERT OR REPLACE INTO extractions
                (observation_id, file, language, file_hash, timestamp, data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result.observation_id,
                result.file,
                result.language,
                result.file_hash,
                result.timestamp,
                data_json,
            ),
        )
        self._conn.commit()

    def get_by_file(self, filepath: str) -> Optional[ExtractionResult]:
        """Retrieve the most recent extraction for a file path."""
        row = self._conn.execute(
            "SELECT * FROM extractions WHERE file = ? ORDER BY timestamp DESC LIMIT 1",
            (filepath,),
        ).fetchone()
        if row is None:
            return None
        return self._deserialize(row["data"])

    def get_by_id(self, observation_id: str) -> Optional[ExtractionResult]:
        """Retrieve an extraction by its observation_id."""
        row = self._conn.execute(
            "SELECT * FROM extractions WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        if row is None:
            return None
        return self._deserialize(row["data"])

    def list_files(self) -> list[str]:
        """Return all distinct file paths with stored extractions."""
        rows = self._conn.execute(
            "SELECT DISTINCT file FROM extractions ORDER BY file"
        ).fetchall()
        return [r["file"] for r in rows]

    def delete_by_file(self, filepath: str) -> bool:
        """Delete stored extraction for a file. Returns True if found and deleted."""
        cur = self._conn.execute("DELETE FROM extractions WHERE file = ?", (filepath,))
        self._conn.commit()
        return cur.rowcount > 0

    def clear(self) -> None:
        """Remove all stored extractions."""
        self._conn.execute("DELETE FROM extractions")
        self._conn.commit()

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _deserialize(self, data_json: str) -> ExtractionResult:
        """Reconstruct an ExtractionResult from stored JSON."""
        d = json.loads(data_json)

        functions = [
            self._deserialize_function(fn) for fn in d.get("functions", [])
        ]
        classes = [
            self._deserialize_class(cls) for cls in d.get("classes", [])
        ]
        imports = [
            ImportStatement(**self._sanitize_import(imp))
            for imp in d.get("imports", [])
        ]

        # Exclude computed fields from ExtractionResult
        result_fields = {
            k: v for k, v in d.items()
            if k not in ("all_dependencies",)
        }
        result_fields["functions"] = functions
        result_fields["classes"] = classes
        result_fields["imports"] = imports

        return ExtractionResult(**result_fields)

    def _deserialize_function(self, fn: dict[str, Any]) -> FunctionSignature:
        """Reconstruct a FunctionSignature from dict."""
        params = [
            Parameter(**self._sanitize_parameter(p))
            for p in fn.get("parameters", [])
        ]
        kwargs = {
            k: v for k, v in fn.items()
            if k not in ("parameters", "qualified_name", "active_pointer")
        }
        kwargs["parameters"] = params
        return FunctionSignature(**kwargs)

    def _deserialize_class(self, cls: dict[str, Any]) -> ClassDefinition:
        """Reconstruct a ClassDefinition from dict."""
        methods = [
            self._deserialize_function(m) for m in cls.get("methods", [])
        ]
        kwargs = {
            k: v for k, v in cls.items()
            if k not in ("methods", "active_pointer")
        }
        kwargs["methods"] = methods
        return ClassDefinition(**kwargs)

    @staticmethod
    def _sanitize_parameter(p: dict[str, Any]) -> dict[str, Any]:
        """Ensure parameter dict has only valid Parameter fields."""
        return {k: v for k, v in p.items() if k in ("name", "type", "default", "optional")}

    @staticmethod
    def _sanitize_import(imp: dict[str, Any]) -> dict[str, Any]:
        """Ensure import dict has only valid ImportStatement fields."""
        return {
            k: v for k, v in imp.items()
            if k in ("module", "names", "alias", "is_wildcard", "line")
        }
