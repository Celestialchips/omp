"""Abstract base class for OMP storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from omp.models import ExtractionResult


class BaseStorage(ABC):
    """Interface for storing and retrieving ExtractionResults.

    Implementations must handle:
    - Saving extraction results (the symbolic layer)
    - Retrieving by file path or observation_id
    - Listing all stored extractions
    - Relational queries across files (dependency graphs, staleness)

    The ``find_by_*`` and ``list_stale`` methods have default implementations
    that perform in-memory filtering over ``list_files`` / ``get_by_file``.
    High-performance backends (e.g. Postgres) should override them with
    native queries.
    """

    # -- Core CRUD (must implement) --

    @abstractmethod
    def save(self, result: ExtractionResult) -> None:
        """Persist an ExtractionResult."""

    @abstractmethod
    def get_by_file(self, filepath: str) -> Optional[ExtractionResult]:
        """Retrieve the most recent extraction for a file path."""

    @abstractmethod
    def get_by_id(self, observation_id: str) -> Optional[ExtractionResult]:
        """Retrieve an extraction by its observation_id."""

    @abstractmethod
    def list_files(self) -> list[str]:
        """Return all file paths that have stored extractions."""

    @abstractmethod
    def delete_by_file(self, filepath: str) -> bool:
        """Delete stored extraction for a file. Returns True if found and deleted."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored extractions."""

    @abstractmethod
    def close(self) -> None:
        """Release any resources (connections, handles)."""

    # -- Relational queries (override for performance) --

    def find_by_dependency(self, module: str) -> list[ExtractionResult]:
        """Find all extractions that import a given module.

        Default implementation scans all stored files. Override in backends
        that support indexed dependency lookups.
        """
        results = []
        for filepath in self.list_files():
            result = self.get_by_file(filepath)
            if result and any(imp.module == module for imp in result.imports):
                results.append(result)
        return results

    def find_by_qualified_name(self, name: str) -> list[ExtractionResult]:
        """Find all extractions containing a function or method with the given qualified name.

        Default implementation scans all stored files. Override in backends
        that support indexed symbol lookups.
        """
        results = []
        for filepath in self.list_files():
            result = self.get_by_file(filepath)
            if not result:
                continue
            for fn in result.functions:
                if fn.qualified_name == name:
                    results.append(result)
                    break
            else:
                for cls in result.classes:
                    if any(m.qualified_name == name for m in cls.methods):
                        results.append(result)
                        break
        return results

    def list_stale(self, current_hashes: dict[str, str]) -> list[str]:
        """Return file paths whose stored ``file_hash`` differs from the provided current hash.

        Args:
            current_hashes: Mapping of ``filepath -> current_file_hash`` to compare against.

        Default implementation scans all stored files. Override in backends
        that support hash comparison at the query level.
        """
        stale = []
        for filepath in self.list_files():
            if filepath in current_hashes:
                result = self.get_by_file(filepath)
                if result and result.file_hash != current_hashes[filepath]:
                    stale.append(filepath)
        return stale

    # -- Context manager --

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
