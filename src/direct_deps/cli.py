from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING
from typing import NamedTuple

from direct_deps.distribution_metadata import get_dependency_lookup_table
from direct_deps.import_analyzer import extract_top_level_imports_from_files
from direct_deps.project_utils import get_python_files
from direct_deps.virtualenv_utils import get_site_packages

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TypeAlias

    from typing_extensions import Any
    from typing_extensions import Protocol

    from direct_deps.distribution_metadata import DistributionMetadata

    ArgV: TypeAlias = "list[str] | tuple[str,...] | None"

    class Subcommand(Protocol):
        @staticmethod
        def arg_parser(
            parser: argparse.ArgumentParser | None = None,
        ) -> argparse.ArgumentParser: ...

        @staticmethod
        def run(args: Any, others: list[str] | None = None) -> int:  # noqa: ANN401
            ...


logger = logging.getLogger("direct-deps")


__prog__ = None


def get_lookup_table(venv: str | None) -> dict[str, DistributionMetadata]:
    site_packages = get_site_packages(venv)
    return get_dependency_lookup_table(site_packages)


def get_direct_dependencies(python_files: Iterable[str], venv: str | None) -> set[str]:
    packages_lookup = get_lookup_table(venv)
    imports = extract_top_level_imports_from_files(python_files)

    packages: set[str] = set()

    for imp in imports:
        if imp in packages_lookup:
            packages.add(packages_lookup[imp].name)

    return packages


class CLI(NamedTuple):
    venv: str | None
    file_or_dir: list[str]

    @classmethod
    def parse_args(cls, argv: ArgV = None) -> CLI:
        parser = argparse.ArgumentParser(
            prog=__prog__, description="Find the direct dependencies of a Python project."
        )
        parser.add_argument(
            "file_or_dir", nargs="+", help="Python files or directories to analyze."
        )
        parser.add_argument(
            "--venv",
            type=str,
            help="The virtualenv directory to analyze.",
        )
        args: CLI = parser.parse_args(argv)  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

        return cls(venv=args.venv, file_or_dir=args.file_or_dir)


def main(argv: ArgV = None) -> int:
    logging.basicConfig(level=logging.INFO)
    args = CLI.parse_args(argv)
    python_files = get_python_files(args.file_or_dir)
    packages = get_direct_dependencies(python_files=python_files, venv=args.venv)

    print("Direct Dependencies:")
    for p in packages:
        print(f" - {p}")

    return 0


if __name__ == "__main__":
    __prog__ = "python3 -m direct_deps"
    raise SystemExit(main())
