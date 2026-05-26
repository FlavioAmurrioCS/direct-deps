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
    from typing_extensions import Protocol

    from direct_deps.distribution_metadata import DistributionMetadata

    class Cmd(Protocol):
        @classmethod
        def arg_parser(
            cls, parser: argparse.ArgumentParser | None = None
        ) -> argparse.ArgumentParser: ...
        def run(self) -> int: ...


logger = logging.getLogger(__name__)


def get_lookup_table(venv: str | None) -> dict[str, DistributionMetadata]:
    site_packages = get_site_packages(venv)
    return get_dependency_lookup_table(site_packages)


class CheckCmd(NamedTuple):
    """Analyze Python files and print the direct dependencies."""

    files: list[str]
    include_jupyter: bool = False
    venv: str | None = None

    @classmethod
    def arg_parser(cls, parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
        parser = parser or argparse.ArgumentParser()
        parser.description = cls.__doc__ or "<PLACEHOLDER_DESCRIPTION>"
        parser.formatter_class = argparse.RawTextHelpFormatter
        # parser.epilog = dedent("""\
        # Example:
        #   %(prog)s <PLACEHOLDER_EXAMPLE>
        # """)
        parser.add_argument("files", nargs="+", help="List of Python files to analyze.")
        parser.add_argument(
            "--include-jupyter",
            action="store_true",
            help="Include Jupyter notebook files when scanning directories.",
        )
        parser.add_argument("--venv", help="Path to the virtual environment.")
        return parser

    def run(self) -> int:
        files = list(get_python_files(self.files, include_jupyter=self.include_jupyter))
        imports = extract_top_level_imports_from_files(files, include_builtin=False)
        table = get_lookup_table(self.venv)
        items: list[str] = []
        for imp in imports:
            if imp in table:
                items.append(table[imp].name)
            else:
                logger.debug("No package found for import: %s", imp)
        for item in sorted(set(items)):
            print(item)
        return 0


class PackageFinderCmd(NamedTuple):
    """Lookup and print the package name for the specified imports."""

    imports: list[str]
    venv: str | None = None

    @classmethod
    def arg_parser(cls, parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
        parser = parser or argparse.ArgumentParser()
        parser.description = cls.__doc__ or "<PLACEHOLDER_DESCRIPTION>"
        parser.formatter_class = argparse.RawTextHelpFormatter
        # parser.epilog = dedent("""\
        # Example:
        #   %(prog)s <PLACEHOLDER_EXAMPLE>
        # """)
        parser.add_argument("imports", nargs="+", help="List of imports to look up.")
        parser.add_argument("--venv", help="Path to the virtual environment.")
        return parser

    def run(self) -> int:
        table = get_lookup_table(self.venv)
        items: list[str] = []
        for item in sorted(set(self.imports)):
            if item in table:
                items.append(table[item].name)
            else:
                logger.debug("No package found for import: %s", item)
        for item in sorted(set(items)):
            print(item)
        return 0


class ExtractImportsCmd(NamedTuple):
    """Extract and print all top-level imports from the specified Python files."""

    files: list[str]
    include_jupyter: bool = False
    include_builtin: bool = False

    @classmethod
    def arg_parser(cls, parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
        parser = parser or argparse.ArgumentParser()
        parser.description = cls.__doc__ or "<PLACEHOLDER_DESCRIPTION>"
        parser.formatter_class = argparse.RawTextHelpFormatter
        # parser.epilog = dedent("""\
        # Example:
        #   %(prog)s <PLACEHOLDER_EXAMPLE>
        # """)
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

    def run(self) -> int:
        files = list(get_python_files(self.files, include_jupyter=self.include_jupyter))
        for imp in extract_top_level_imports_from_files(
            files, include_builtin=self.include_builtin
        ):
            print(imp)
        return 0


################################################################################
# endregion: Commands
################################################################################

SUB_COMMANDS: dict[str, type[Cmd]] = {
    "check": CheckCmd,
    "extract-imports": ExtractImportsCmd,
    "find-package": PackageFinderCmd,
}

VERSION = "0.1.0"

__prog__ = None


def main(argv: list[str] | tuple[str, ...] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=__prog__)
    parser.description = dedent("""\
        Tool to analyze direct dependencies of Python projects.
    """).rstrip()
    parser.formatter_class = lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=30)
    parser.epilog = dedent("""\
    Examples:
        %(prog)s check src/main.py src/utils.py --venv ./venv
        %(prog)s find-package requests numpy --venv ./venv
        %(prog)s extract-imports src/main.py src/utils.py
    """)
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity level."
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command")
    for cmd_name, cmd in SUB_COMMANDS.items():
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd.__doc__ or None)
        cmd.arg_parser(cmd_parser)
    args = parser.parse_args(argv)
    command: str | None = args.command
    verbose: int = args.verbose
    if command is None:
        # NOTE: You can also set a default command here if desired
        parser.print_help()
        return 1
    logging.basicConfig(
        level=logging.WARNING - (verbose * 10),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cls = SUB_COMMANDS[command]

    excluded_args = ("command", "verbose")
    cmd_instance = cls(**{k: v for k, v in vars(args).items() if k not in excluded_args})
    return cmd_instance.run()


if __name__ == "__main__":
    __prog__ = "python3 -m direct_deps"
    raise SystemExit(main())
