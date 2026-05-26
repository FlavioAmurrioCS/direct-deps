from __future__ import annotations

import glob
import logging
import os
import shutil
import site
import subprocess

logger = logging.getLogger("direct-deps")


def current_virtual_environment() -> str | None:
    venv = os.environ.get("VIRTUAL_ENV")
    if venv and os.path.isdir(venv):
        logger.info("Using virtualenv from VIRTUAL_ENV: %s", venv)
        return venv
    return None


def get_hatch_env() -> str | None:
    if os.path.isfile("pyproject.toml") and shutil.which("hatch"):
        result = subprocess.run(
            ("hatch", "env", "find", "hatch-test"),  # noqa: RUF100, S603, S607
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if os.path.isdir(line):
                    logger.info("Using Hatch virtual environment: %s", line)
                    return line
    return None


def get_pipenv_virtualenv() -> str | None:
    if os.path.isfile("Pipfile"):
        result = subprocess.run(("pipenv", "--venv"), capture_output=True, text=True, check=False)  # noqa: RUF100, S603, S607
        if result.returncode == 0:
            logger.info("Using Pipenv virtual environment: %s", result.stdout.strip())
            return result.stdout.strip()
    return None


def get_local_virtualenv() -> str | None:
    if os.path.isdir(".venv"):
        logger.info("Using local virtual environment: %s", ".venv")
        return ".venv"
    if os.path.isdir("venv"):
        logger.info("Using local virtual environment: %s", "venv")
        return "venv"
    return None


def find() -> str | None:
    return (
        None
        or current_virtual_environment()
        or get_local_virtualenv()
        or get_hatch_env()
        or get_pipenv_virtualenv()
        or None
    )


def get_site_packages(venv: str | None) -> list[str]:
    if venv and not os.path.isdir(venv):
        msg = f"Virtual environment directory '{venv}' does not exist or is not a directory."
        raise ValueError(msg)

    venv = venv or find()
    if not venv:
        logger.warning("No virtual environment found. Using system site-packages.")
        return site.getsitepackages()

    directory = os.path.join(venv, "lib", "*", "site-packages")
    site_packages = [x for x in glob.iglob(directory) if os.path.isdir(x)]
    if not site_packages:
        logger.warning(
            "No site-packages found in virtual environment '%s'. "
            "Ensure the virtual environment is set up correctly.",
            venv,
        )
    return site_packages
