from __future__ import annotations

import ast
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable

logger = logging.getLogger("direct-deps")


def _extract_import(file: str) -> Generator[str]:
    try:
        with open(file) as f:
            tree = ast.parse(f.read(), filename=file)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to parse file %s: %s", file, e)
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def extract_top_level_imports_from_python_files(files: Iterable[str]) -> Generator[str]:
    seen = set()
    for file in files:
        for imp in _extract_import(file):
            normalized_imp = imp.split(".")[0]
            if normalized_imp not in seen:
                seen.add(normalized_imp)
                yield normalized_imp


if __name__ == "__main__":
    for imp in extract_top_level_imports_from_python_files([__file__]):
        print(imp)
