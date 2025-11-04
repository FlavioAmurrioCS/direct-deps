from __future__ import annotations

import ast
import json
import logging
import sys
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable
    from typing import TypedDict

    class JupyterNotebookCell(TypedDict):
        cell_type: str
        source: list[str]

    class JupyterNotebook(TypedDict):
        cells: list[JupyterNotebookCell]


logger = logging.getLogger("direct-deps")


def parse_python_content(content: str, filename: str = "<unknown>") -> Generator[ast.AST]:
    """Convert Python source code to AST nodes."""
    try:
        yield ast.parse(content, filename=filename)
    except SyntaxError as e:
        logger.warning("Failed to parse file %s: %s", filename, e)


def parse_notebook_content(
    content: JupyterNotebook, filename: str = "<unknown>"
) -> Generator[ast.AST]:
    """Convert a Jupyter notebook to AST nodes."""
    for i, cell in enumerate(content["cells"]):
        if cell["cell_type"] != "code":
            continue
        source_code = "".join(
            (line if not line.lstrip().startswith(("%", "!")) else f"# {line}")
            for line in cell["source"]
        )
        try:
            yield ast.parse(source_code, filename=f"{filename} (cell {i})")
        except SyntaxError as e:
            logger.warning("Failed to parse code cell in %s: %s", filename, e)
            continue


def get_imports_from_ast(tree: ast.AST) -> Generator[str]:
    """Extract import statements from an AST tree."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def parse_file_to_ast(filename: str) -> Generator[ast.AST]:
    """Convert a file (Python or Jupyter notebook) to AST nodes."""
    with open(filename) as f:
        text = f.read()
    if filename.endswith(".py"):
        yield from parse_python_content(text, filename=filename)
    elif filename.endswith(".ipynb"):
        notebook: JupyterNotebook = json.loads(text)
        yield from parse_notebook_content(notebook, filename=filename)
    else:
        try:
            notebook = json.loads(text)
            yield from parse_notebook_content(notebook, filename=filename)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse notebook %s: %s", filename, e)
        else:
            yield from parse_python_content(text, filename=filename)


def get_top_level_imports(filename: str) -> list[str]:
    """Get top-level imports from a file (Python or Jupyter notebook)."""
    return sorted(
        {
            imp.split(".")[0]
            for _ast in parse_file_to_ast(filename)
            for imp in get_imports_from_ast(_ast)
        }
    )


@lru_cache(maxsize=1)
def builtin_module_names() -> set[str]:
    """Get the set of built-in module names."""
    if sys.version_info >= (3, 10):
        return sys.stdlib_module_names  # type: ignore[attr-defined]
    return set()


def extract_top_level_imports_from_files(
    files: Iterable[str], *, include_builtin: bool = False
) -> Generator[str]:
    """Extract unique top-level imports from a list of Python files."""
    seen = set()
    for file in files:
        logger.debug("Extracting imports from file: %s", file)
        for imp in get_top_level_imports(file):
            if imp not in seen:
                seen.add(imp)
                if not include_builtin and imp in builtin_module_names():
                    continue
                yield imp


if __name__ == "__main__":
    for f in [__file__]:
        print(f"Imports in {f}:")
        for imp in get_top_level_imports(f):
            print(f"  {imp}")
