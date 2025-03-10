# direct-deps

[![PyPI - Version](https://img.shields.io/pypi/v/direct-deps.svg)](https://pypi.org/project/direct-deps)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/direct-deps.svg)](https://pypi.org/project/direct-deps)

-----

## Table of Contents

- [direct-deps](#direct-deps)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Inside your project's virtualenv](#inside-your-projects-virtualenv)
    - [Installed outside your virtualenv](#installed-outside-your-virtualenv)
    - [Recommendation](#recommendation)
  - [Limitations](#limitations)
  - [License](#license)

## Introduction
A utility to analyze a Python project and its virtual environment to identify direct dependencies. Helps you keep your dependency list lean and accurate.

## Installation

```console
pip install direct-deps
```

## Usage

### Inside your project's virtualenv
```bash
source venv/bin/activate
pip install direct-deps
#  No need to specify venv since direct-deps can detect the virtualenv if installed in it.
direct-deps .
```

### Installed outside your virtualenv
```bash
pipx install direct-deps

# You must pass in the location of your virtualenv
# hatch: hatch env find
# pipenv: pipenv --venv
direct-deps . --venv venv
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
[flavio@Mac ~/dev/github.com/FlavioAmurrioCS/comma-cli]
$ hatch shell
source "/Users/flavio/Library/Application Support/hatch/env/virtual/comma-cli/NLCv5VCj/comma-cli/bin/activate"

(comma-cli)
[flavio@Mac ~/dev/github.com/FlavioAmurrioCS/comma-cli]
$ pip install direct-deps
...

(comma-cli)
[flavio@Mac ~/dev/github.com/FlavioAmurrioCS/comma-cli]
$ direct-deps src
Direct Dependencies:
 - persistent-cache-decorator
 - requests
 - rich
 - setuptools-scm
 - typedfzf
 - typer

(comma-cli)
[flavio@Mac ~/dev/github.com/FlavioAmurrioCS/comma-cli]
$ direct-deps tests
Direct Dependencies:
 - pytest
 - runtool
 - tomlkit
 - typer

# So my [packages] would be
  persistent-cache-decorator
  requests
  rich
  setuptools-scm
  typedfzf
  typer

# And my [dev-packages] would be, notice that since typer is a main dependency, there is no need to list it in this section.
  pytest
  runtool
  tomlkit
```

## Limitations
This tool relies on being able to look at the `import <package>` and `from <package> import ...` as
well as use your virtualenv to find the appropiate package name. This means that that anything
not imported directly will not appear the the list such as plugins (pytest-cov) and static analysis tools(ruff, pre-commit).

## License

`direct-deps` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
