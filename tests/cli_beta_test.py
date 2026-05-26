from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from direct_deps import cli_beta
from direct_deps.cli_beta import CheckCmd
from direct_deps.cli_beta import ExtractImportsCmd
from direct_deps.cli_beta import PackageFinderCmd
from direct_deps.cli_beta import main

if TYPE_CHECKING:
    from pathlib import Path

RC_OK = 0
RC_NO_COMMAND = 1


def _make_dist(site_packages: Path, dist_name: str, top_levels: list[str]) -> None:
    dist_info = site_packages / f"{dist_name}-1.0.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "METADATA").write_text(f"Name: {dist_name}\n", encoding="utf-8")
    (dist_info / "RECORD").write_text("", encoding="utf-8")
    (dist_info / "top_level.txt").write_text("\n".join(top_levels) + "\n", encoding="utf-8")


@pytest.fixture
def fake_venv(tmp_path: Path) -> str:
    site_packages = tmp_path / "venv" / "lib" / "python" / "site-packages"
    site_packages.mkdir(parents=True)
    _make_dist(site_packages, "requests", ["requests"])
    _make_dist(site_packages, "PyYAML", ["yaml", "_yaml"])
    return str(tmp_path / "venv")


def test_check_outputs_sorted_deduped_bare_names(
    fake_venv: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("import requests\nimport yaml\nimport os\n", encoding="utf-8")
    (src / "b.py").write_text("import requests\n", encoding="utf-8")

    rc = CheckCmd(paths=[str(src)], venv=fake_venv).run()

    assert rc == RC_OK
    # Sorted (PyYAML before requests), deduped, no header/prefix, stdlib (os) dropped.
    assert capsys.readouterr().out == "PyYAML\nrequests\n"


def test_find_package_resolves_import_names(
    fake_venv: str, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = PackageFinderCmd(imports=["yaml", "requests", "nonexistent"], venv=fake_venv).run()

    assert rc == RC_OK
    # Unmatched import is skipped; output is sorted distribution names.
    assert capsys.readouterr().out == "PyYAML\nrequests\n"


def test_extract_imports_filters_stdlib_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = tmp_path / "m.py"
    module.write_text("import os\nimport requests\n", encoding="utf-8")

    rc = ExtractImportsCmd(paths=[str(module)]).run()

    assert rc == RC_OK
    out = capsys.readouterr().out.split()
    assert "requests" in out
    assert "os" not in out


def test_extract_imports_includes_stdlib_when_requested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    module = tmp_path / "m.py"
    module.write_text("import os\nimport requests\n", encoding="utf-8")

    rc = ExtractImportsCmd(paths=[str(module)], include_builtin=True).run()

    assert rc == RC_OK
    out = capsys.readouterr().out.split()
    assert "os" in out
    assert "requests" in out


def test_main_check_dispatch(
    fake_venv: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("import requests\n", encoding="utf-8")

    rc = main(["check", str(src), "--venv", fake_venv])

    assert rc == RC_OK
    assert capsys.readouterr().out == "requests\n"


def test_main_without_command_returns_nonzero() -> None:
    assert main([]) == RC_NO_COMMAND


def test_get_version_returns_installed_version() -> None:
    assert cli_beta.get_version()
