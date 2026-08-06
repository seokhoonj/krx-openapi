"""``python -m krx_openapi`` -- same entry point as the ``krx`` command."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
