"""OMP Storage - Persistence backends for the Symbolic Layer."""

from omp.storage.base import BaseStorage
from omp.storage.sqlite import SQLiteStorage

__all__ = ["BaseStorage", "SQLiteStorage"]
