from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from typing import NamedTuple

prog = None


class PackageDistInfo(NamedTuple):
    name: str
    top_level: list[str]

    @classmethod
    def from_dir(cls, d: str) -> PackageDistInfo:
        top_level_file = os.path.join(d, "top_level.txt")
        record_file = os.path.join(d, "RECORD")
        metadata_file = os.path.join(d, "METADATA")

        with open(metadata_file) as f:
            for line in f:
                if line.startswith("Name: "):
                    name = line.split(": ")[1].strip()
                    break
            else:
                msg = "No name found in METADATA"
                raise ValueError(msg)

        top_level: set[str] = set()
        with open(record_file) as f:
            for line in f:
                file = line.split(",")[0]
                if file.endswith(".py"):
                    top_level.add(file.split(os.sep)[0])

        if os.path.exists(top_level_file):
            with open(top_level_file) as f:
                top_level.update(x.strip() for x in f)

        return cls(name, list(top_level))


def get_packages(site_packages: list[str]) -> dict[str, PackageDistInfo]:
    ret: dict[str, PackageDistInfo] = {}
    for site_package in site_packages:
        for site_package_file in (os.path.join(site_package, x) for x in os.listdir(site_package)):
            if site_package_file.endswith(".dist-info"):
                p = PackageDistInfo.from_dir(site_package_file)
                for top_level in p.top_level:
                    ret[top_level] = p
    return ret


def _get_import_lines(files: list[str]) -> Generator[str]:
    for file in files:
        with open(file) as f:
            for _line in f:
                line = _line.strip()
                if line.startswith(("import ", "from ")):
                    yield line


def get_imports(files: list[str]) -> set[str]:
    return {line.split()[1].split(".")[0] for line in _get_import_lines(files)}


# NOTE: Do some file filtering
def get_python_files(project_dir: str) -> list[str]:
    import subprocess

    if os.path.exists(os.path.join(project_dir, ".git")):
        files = subprocess.run(  # noqa: S603
            ("git", "ls-files", "*.py"), capture_output=True, check=True, text=True, cwd=project_dir
        ).stdout.splitlines()

        return [os.path.join(project_dir, x) for x in files]

    return [x.as_posix() for x in Path(project_dir).rglob("*.py") if x.is_file()]


def runner(project_dir: str, site_packages: list[str]) -> list[str]:
    python_files = get_python_files(project_dir)
    packages_lookup = get_packages(site_packages)
    imports = get_imports(python_files)

    packages: set[str] = set()

    for imp in imports:
        if imp in packages_lookup:
            packages.add(packages_lookup[imp].name)

    return sorted(packages)


def main(argv: list[str] | tuple[str, ...] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog=prog, description="Find the direct dependencies of a Python project."
    )
    parser.add_argument(
        "project_dir",
        type=str,
        help="The project directory to analyze.",
    )
    parser.add_argument(
        "--venv",
        type=str,
        help="The virtualenv directory to analyze.",
    )

    args = parser.parse_args(argv)

    project_dir = args.project_dir
    if args.venv:
        from glob import iglob

        directory = os.path.join(args.venv, "lib", "*", "site-packages")
        site_packages = [x for x in iglob(directory) if os.path.isdir(x)]
    else:
        import site

        site_packages = site.getsitepackages()

    results = runner(project_dir, site_packages)

    print("Direct Dependencies:")
    for p in results:
        print(f" - {p}")

    return 0


if __name__ == "__main__":
    prog = "python3 -m direct_deps"
    raise SystemExit(main())
