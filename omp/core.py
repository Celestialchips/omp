"""
OMP Core - Main dispatcher for the Open Memory Protocol package.

Provides the public API for:
- Extracting from a single file
- Extracting from source code string
- Scanning an entire project directory
- Checking staleness of a previous extraction
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Optional

from omp.models import (
    ExtractionResult,
    FunctionSignature,
    ClassDefinition,
    StalenessReport,
    ProjectExtractionResult,
)
from omp.parsers import (
    get_parser,
    EXTRACTORS,
    EXTENSION_MAP,
    supported_extensions,
)


def extract_from_source(
    source: str | bytes,
    language: str,
    file: str = "<source>",
) -> ExtractionResult:
    """
    Extract function signatures, classes, and imports from source code.

    Args:
        source: The source code as a string or bytes.
        language: Language identifier (e.g. "python", "typescript", "javascript", "go", "tsx").
        file: Optional filename for the result; defaults to "<source>".

    Returns:
        ExtractionResult with functions, classes, imports, and file_hash.

    Raises:
        ValueError: If the language is not supported.
    """
    if isinstance(source, str):
        source_bytes = source.encode("utf-8")
    else:
        source_bytes = source

    if language not in EXTRACTORS:
        raise ValueError(
            f"Unsupported language: {language}. Available: {list(EXTRACTORS.keys())}"
        )

    parser = get_parser(language)
    tree = parser.parse(source_bytes)
    extractor = EXTRACTORS[language]
    functions, classes, imports = extractor(tree.root_node)

    file_hash = hashlib.sha256(source_bytes).hexdigest()[:16]

    return ExtractionResult(
        file=file,
        language=language,
        functions=functions,
        classes=classes,
        imports=imports,
        file_hash=file_hash,
    )


def extract_from_file(filepath: str | Path) -> ExtractionResult:
    """
    Extract function signatures, classes, and imports from a file.

    Auto-detects language from file extension. Sets the file path on the result
    and on every function, class, and method for cross-file lookups.

    Args:
        filepath: Path to the source file.

    Returns:
        ExtractionResult with all extracted symbols and file_hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    ext = path.suffix
    exts = supported_extensions()
    if ext not in exts:
        raise ValueError(
            f"Unsupported file extension: {ext}. Supported: {exts}"
        )

    language = EXTENSION_MAP[ext]
    parser = get_parser(language)
    source_bytes = path.read_bytes()
    tree = parser.parse(source_bytes)
    extractor = EXTRACTORS[language]
    functions, classes, imports = extractor(tree.root_node)

    file_hash = hashlib.sha256(source_bytes).hexdigest()[:16]
    file_str = str(path)

    # Attach file path to every function and class/method
    for fn in functions:
        fn.file = file_str
    for cls in classes:
        cls.file = file_str
        for method in cls.methods:
            method.file = file_str

    return ExtractionResult(
        file=file_str,
        language=language,
        functions=functions,
        classes=classes,
        imports=imports,
        file_hash=file_hash,
    )


_DEFAULT_EXCLUDE_DIRS = frozenset({
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".tox",
    "vendor",
})


def extract_project(
    root_dir: str | Path,
    exclude_dirs: set[str] | None = None,
) -> ProjectExtractionResult:
    """
    Recursively scan a project directory and extract from all supported files.

    Skips files that fail to parse (logs a warning to stderr and continues).
    Results are sorted by file path for deterministic output.

    Args:
        root_dir: Root directory to scan.
        exclude_dirs: Directories to skip when walking. Defaults to common
            build/cache directories (node_modules, .git, __pycache__, etc.).

    Returns:
        ProjectExtractionResult with all file extractions.
    """
    root = Path(root_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    exts = set(supported_extensions())
    if exclude_dirs is None:
        exclude_dirs = _DEFAULT_EXCLUDE_DIRS

    results: list[ExtractionResult] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in exts:
            continue
        # Skip if any parent directory is in exclude_dirs
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        parts = rel.parts
        if any(part in exclude_dirs for part in parts[:-1]):
            continue

        try:
            result = extract_from_file(path)
            results.append(result)
        except Exception as e:
            print(f"Warning: Failed to parse {path}: {e}", file=sys.stderr)

    results.sort(key=lambda r: r.file)

    return ProjectExtractionResult(root=str(root), files=results)


def _get_function_qualified_names_and_hashes(
    result: ExtractionResult,
) -> dict[str, str]:
    """Build qualified_name -> ast_hash for all functions and methods."""
    mapping: dict[str, str] = {}
    for fn in result.functions:
        mapping[fn.qualified_name] = fn.ast_hash or ""
    for cls in result.classes:
        for method in cls.methods:
            mapping[method.qualified_name] = method.ast_hash or ""
    return mapping


def check_staleness(
    previous: ExtractionResult,
    filepath: str | Path | None = None,
) -> StalenessReport:
    """
    Check whether a stored ExtractionResult is stale compared to the current file.

    Compares file hashes first; if they differ, re-extracts and compares
    function/method qualified names and AST hashes to report what changed,
    was removed, or was added.

    Args:
        previous: The previously stored extraction result.
        filepath: Path to the file. If None, uses previous.file (must not be "<source>").

    Returns:
        StalenessReport with is_stale flag and change details.

    Raises:
        ValueError: If filepath is None and previous.file is "<source>".
        FileNotFoundError: If the file does not exist.
    """
    path_str = str(filepath) if filepath is not None else previous.file
    if path_str == "<source>":
        raise ValueError(
            "check_staleness requires a file path; previous.file is '<source>'"
        )

    path = Path(path_str).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    current_bytes = path.read_bytes()
    current_hash = hashlib.sha256(current_bytes).hexdigest()[:16]

    if current_hash == previous.file_hash:
        return StalenessReport(
            file=path_str,
            is_stale=False,
            stored_file_hash=previous.file_hash,
            current_file_hash=current_hash,
        )

    # Re-extract and diff
    current = extract_from_file(path)
    return diff_extractions(previous, current)


def diff_extractions(old: ExtractionResult, new: ExtractionResult) -> StalenessReport:
    """
    Compare two ExtractionResult objects and report differences.

    A utility that compares two in-memory extractions without reading files.
    Returns a StalenessReport with changed, removed, and added functions/methods
    based on qualified_name and ast_hash.

    Args:
        old: The previous extraction.
        new: The current extraction.

    Returns:
        StalenessReport with is_stale=True and detailed change lists.
    """
    old_map = _get_function_qualified_names_and_hashes(old)
    new_map = _get_function_qualified_names_and_hashes(new)

    old_names = set(old_map.keys())
    new_names = set(new_map.keys())

    removed_functions = sorted(old_names - new_names)
    added_functions = sorted(new_names - old_names)
    changed_functions = sorted(
        qn for qn in (old_names & new_names)
        if old_map[qn] != new_map[qn]
    )

    is_stale = bool(removed_functions or added_functions or changed_functions)

    return StalenessReport(
        file=new.file,
        is_stale=is_stale,
        stored_file_hash=old.file_hash,
        current_file_hash=new.file_hash,
        changed_functions=changed_functions,
        removed_functions=removed_functions,
        added_functions=added_functions,
    )
