from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable

    from typing_extensions import TypeAlias

    ArgV: TypeAlias = "list[str] | tuple[str,...] | None"


logger = logging.getLogger("direct-deps")


def get_python_files(paths: Iterable[str], *, include_jupyter: bool = False) -> Generator[str]:
    for path in paths:
        abs_path = os.path.realpath(path)
        if os.path.isfile(abs_path):
            yield abs_path
        elif os.path.isdir(abs_path):
            yield from (
                x.as_posix()
                for x in Path(abs_path).rglob("*.py")
                if "site-packages" not in x.as_posix()
            )
            if include_jupyter:
                yield from (
                    x.as_posix()
                    for x in Path(abs_path).rglob("*.ipynb")
                    if "site-packages" not in x.as_posix()
                )
        else:
            logger.info("Path does not exist: %s", abs_path)


# # NOTE: Do some file filtering
# def get_python_files(project_dir: str) -> list[str]:
#     import subprocess

#     if os.path.exists(os.path.join(project_dir, ".git")):
#         files = subprocess.run(
#             ("git", "ls-files", "*.py"), capture_output=True,
#             check=True, text=True, cwd=project_dir
#         ).stdout.splitlines()

#         return [os.path.join(project_dir, x) for x in files]

#     return [x.as_posix() for x in Path(project_dir).rglob("*.py") if x.is_file()]


if __name__ == "__main__":
    for file in get_python_files(["."]):
        print(file)
