# direct-deps

[![PyPI - Version](https://img.shields.io/pypi/v/direct-deps.svg)](https://pypi.org/project/direct-deps)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/direct-deps.svg)](https://pypi.org/project/direct-deps)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/FlavioAmurrioCS/direct-deps/main.svg)](https://results.pre-commit.ci/latest/github/FlavioAmurrioCS/direct-deps/main)

-----

## Table of Contents

- [direct-deps](#direct-deps)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Installation](#installation)
  - [Usage](#usage)
    - [`check` (primary)](#check-primary)
    - [`extract-imports`](#extract-imports)
    - [`find-package`](#find-package)
  - [Limitations](#limitations)
  - [License](#license)

## Introduction
A utility to analyze a Python project and its virtual environment to identify direct dependencies. Helps you keep your dependency list lean and accurate.

The tool automatically detects common virtual environment setups including:
- Current activated virtual environment (`$VIRTUAL_ENV`)
- Local `.venv` or `venv` directories
- Hatch environments
- Pipenv environments

## Installation

Installation is optional! You can run `direct-deps` without installing it using `uvx` or `pipx run`.

```console
# Optional: Install globally
pipx install direct-deps

# or
uv tool install direct-deps
```

## Usage

`direct-deps` exposes three subcommands — `check`, `extract-imports`, and `find-package`.
The recommended way to run any of them is without installation via `uvx` or `pipx run`.
Every command accepts one or more **files or directories** (directories are scanned
recursively).

### `check` (primary)
The main command: it lists your project's direct dependencies. Run it directly without
installation — the tool will automatically detect your project's virtual environment:

```bash
# Using uvx (uv's tool runner)
uvx direct-deps check .

# Using pipx
pipx run direct-deps check .

# Or analyze specific directories
uvx direct-deps check src
uvx direct-deps check tests
```

To split packages and dev-packages you can do the following.

```bash
# Sample Project Structure
├── pyproject.toml
├── src
│   └── comma-cli
│       └── ...
└── tests
    └── ...
```

```bash
$ uvx direct-deps check src
persistent-cache-decorator
requests
rich
setuptools-scm
typedfzf
typer

$ uvx direct-deps check tests
pytest
runtool
tomlkit
typer

# So my [project.dependencies] would be:
[project]
dependencies = [
  "persistent-cache-decorator",
  "requests",
  "rich",
  "setuptools-scm",
  "typedfzf",
  "typer",
]

# And my [project.optional-dependencies.dev] would be (notice that since typer is a main dependency, there is no need to list it here):
[project.optional-dependencies]
dev = [
  "pytest",
  "runtool",
  "tomlkit",
]
```

### `extract-imports`
Lists every unique top-level import found in the given files or directories. This is the
raw input that `check` resolves against your environment, so it's useful for debugging what
the tool actually detected. Standard-library modules are excluded by default (pass
`--include-builtin` to include them, and `--include-jupyter` to scan notebooks).

```bash
$ uvx direct-deps extract-imports src
persistent_cache_decorator
requests
rich
typedfzf
typer
```

### `find-package`
Resolves one or more import/module names to the distribution (package) names that provide
them, using your environment's metadata. Handy when an import name differs from its PyPI
package name (e.g. `yaml` is provided by `PyYAML`).

```bash
$ uvx direct-deps find-package yaml requests
PyYAML
requests
```

## Limitations
This tool relies on being able to look at the `import <package>` and `from <package> import ...` as
well as use your virtualenv to find the appropriate package name. This means that anything
not imported directly will not appear in the list such as plugins (pytest-cov) and static analysis tools (ruff, pre-commit).

## License

`direct-deps` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
