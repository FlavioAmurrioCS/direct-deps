from __future__ import annotations

import argparse
import logging
from textwrap import dedent
from typing import TYPE_CHECKING
from typing import NamedTuple

from direct_deps.distribution_metadata import get_dependency_lookup_table
from direct_deps.import_analyzer import extract_top_level_imports_from_files
from direct_deps.project_utils import get_python_files
from direct_deps.virtualenv_utils import get_site_packages

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typing_extensions import Any
    from typing_extensions import Protocol
    from typing_extensions import TypeAlias

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


__PROG__ = None


def get_lookup_table(venv: str | None) -> dict[str, DistributionMetadata]:
    site_packages = get_site_packages(venv)
    return get_dependency_lookup_table(site_packages)


def get_direct_dependencies(python_files: Iterable[str], venv: str | None) -> set[str]:
    packages_lookup = get_lookup_table(venv )
    imports = extract_top_level_imports_from_files(python_files)

    packages: set[str] = set()

    for imp in imports:
        if imp in packages_lookup:
            packages.add(packages_lookup[imp].name)

    return packages


class Analyze(NamedTuple):
    files: list[str]
    include_jupyter: bool = False
    venv: str | None = None

    @staticmethod
    def arg_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
        parser = parser or argparse.ArgumentParser()
        parser.add_argument("files", nargs="+", help="List of Python files to analyze.")
        parser.add_argument(
            "--include-jupyter",
            action="store_true",
            help="Include Jupyter notebook files when scanning directories.",
        )
        parser.add_argument("--venv", help="Path to the virtual environment.")
        return parser

    @staticmethod
    def run(args: Analyze, others: list[str] | None = None) -> int:  # noqa: ARG004
        files = list(get_python_files(args.files, include_jupyter=args.include_jupyter))
        imports = extract_top_level_imports_from_files(files, include_builtin=False)
        table = get_lookup_table(args.venv)
        for imp in imports:
            if imp in table:
                print(table[imp].name)
            else:
                logger.debug("No package found for import: %s", imp)
        return 0


class Lookup(NamedTuple):
    imports: list[str]
    venv: str | None = None

    @staticmethod
    def arg_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
        parser = parser or argparse.ArgumentParser()
        parser.description = (  # pyrefly: ignore[implicitly-defined-attribute]
            "Look up packages for given imports."
        )
        parser.add_argument("imports", nargs="+", help="List of imports to look up.")
        parser.add_argument("--venv", help="Path to the virtual environment.")
        return parser

    @staticmethod
    def run(args: Lookup, others: list[str] | None = None) -> int:  # noqa: ARG004
        table = get_lookup_table(args.venv)
        for item in args.imports:
            if item in table:
                print(table[item].name)
            else:
                logger.debug("No package found for import: %s", item)
        return 0


class Imports(NamedTuple):
    files: list[str]
    include_jupyter: bool = False
    include_builtin: bool = False

    @staticmethod
    def arg_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
        parser = parser or argparse.ArgumentParser()
        parser.description = "Extract top-level imports from Python files."  # pyrefly: ignore[implicitly-defined-attribute]  # noqa: E501
        parser.add_argument("files", nargs="+", help="List of Python files to analyze.")
        parser.add_argument(
            "--include-jupyter",
            action="store_true",
            help="Include Jupyter notebook files when scanning directories.",
        )
        parser.add_argument(
            "--include-builtin", action="store_true", help="Include built-in modules."
        )
        return parser

    @staticmethod
    def run(args: Imports, others: list[str] | None = None) -> int:  # noqa: ARG004
        files = list(get_python_files(args.files, include_jupyter=args.include_jupyter))
        for imp in extract_top_level_imports_from_files(
            files, include_builtin=args.include_builtin
        ):
            print(imp)
        return 0


def main2(argv: ArgV = None) -> int:
    parser = argparse.ArgumentParser(
        prog=__PROG__,
        description="Tool to analyze direct dependencies of Python projects.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=dedent("""\
        Examples:
        %(prog)s analyze src/main.py src/utils.py --venv ./venv
        %(prog)s lookup requests numpy --venv ./venv
        %(prog)s imports src/main.py src/utils.py
        """),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    subparsers = parser.add_subparsers(
        dest="command", required=True, description="Available subcommands"
    )
    subcommands: dict[str, Subcommand] = {
        "analyze": Analyze,
        "lookup": Lookup,
        "imports": Imports,
    }
    for name, cmd in subcommands.items():
        _parser = subparsers.add_parser(name)
        cmd.arg_parser(_parser)

    args, others = parser.parse_known_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cmd_class = subcommands[args.command or "analyze"]
    return cmd_class.run(args, others)


class CLI(NamedTuple):
    venv: str | None
    file_or_dir: list[str]

    @classmethod
    def parse_args(cls, argv: ArgV = None) -> CLI:
        parser = argparse.ArgumentParser(
            prog=__PROG__, description="Find the direct dependencies of a Python project."
        )
        parser.add_argument(
            "file_or_dir", nargs="+", help="Python files or directories to analyze."
        )
        parser.add_argument(
            "--venv",
            type=str,
            help="The virtualenv directory to analyze.",
        )
        args: CLI = parser.parse_args(argv)  # type: ignore[assignment]

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
    __PROG__ = "python3 -m direct_deps"
    raise SystemExit(main2())
