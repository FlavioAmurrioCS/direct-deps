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
    - [Run without installation (Recommended)](#run-without-installation-recommended)
    - [Recommendation](#recommendation)
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
```

## Usage

### Run without installation (Recommended)
The easiest way to use `direct-deps` is to run it directly without installation. The tool will automatically detect your project's virtual environment:

```bash
# Using uvx (uv's tool runner)
uvx direct-deps .

# Using pipx
pipx run direct-deps .

# Or analyze specific directories
uvx direct-deps src
uvx direct-deps tests
```

### Recommendation
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
$ uvx direct-deps src
Direct Dependencies:
 - persistent-cache-decorator
 - requests
 - rich
 - setuptools-scm
 - typedfzf
 - typer

$ uvx direct-deps tests
Direct Dependencies:
 - pytest
 - runtool
 - tomlkit
 - typer

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

## Limitations
This tool relies on being able to look at the `import <package>` and `from <package> import ...` as
well as use your virtualenv to find the appropriate package name. This means that anything
not imported directly will not appear in the list such as plugins (pytest-cov) and static analysis tools (ruff, pre-commit).

## License

`direct-deps` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
