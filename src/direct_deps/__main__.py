from __future__ import annotations


def main(argv: list[str] | tuple[str, ...] | None = None) -> int:
    from direct_deps.cli_beta import main as _main

    return _main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
