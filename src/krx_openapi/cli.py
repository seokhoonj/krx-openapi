"""Command-line shell over ``KRX`` -- the same names as the Python client.

The CLI mirrors the accessor tree one-to-one, so a call reads the same on both
sides: ``krx.index.kospi("20200414")`` is ``krx index kospi 20200414``. No api_ids
to memorize -- the readable ``group name`` pair selects the service. ``list`` and
``fields`` browse the bundled catalog offline (no key); ``get`` is the escape hatch
that still takes a raw ``category`` + ``api_id``.

    $ krx index kospi 20200414
    $ krx stock daily 20200414 --market KOSDAQ
    $ krx bond treasury 20200414 --json
    $ krx list                      # every group and its methods (offline)
    $ krx fields index kospi         # the columns that service returns (offline)
    $ krx get idx krx_dd_trd --date 20200414   # any service, by raw ids
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from collections.abc import Callable, Sequence

from . import __version__, catalog
from .client import KRX
from .errors import KRXError
from .types import Row

_PROG = "krx"
_ERROR_PREFIX = f"{_PROG}: "

# How many rows the text view prints; the full result is always in --json.
_MAX_SHOWN_ROWS = 20


def main(argv: Sequence[str] | None = None) -> int:
    """Parse ``argv``, run one call, and return a process exit code.

    A failure -- a missing/rejected key, a vendor error, or a transport problem -- is
    printed as a one-line ``krx: <message>`` to stderr and returns 1. A usage error
    (a bad flag or subcommand, via argparse) returns 2.
    """
    args = _make_parser().parse_args(argv)
    run: Callable[[argparse.Namespace], int] = args.run
    try:
        return run(args)
    except KRXError as err:
        print(f"{_ERROR_PREFIX}{err}", file=sys.stderr)
        return 1


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG, description="Read the KRX Open API from the command line.")
    parser.add_argument("--version", action="version", version=f"{_PROG} {__version__}")
    commands = parser.add_subparsers(required=True)

    # One subcommand per accessor group: `krx <group> <name> <date>`.
    for group in catalog.groups():
        fetch = commands.add_parser(group, help=f"{group} services")
        fetch.add_argument("name", choices=catalog.methods(group), help="service method")
        fetch.add_argument("date", metavar="YYYYMMDD", help="trade date (basDd)")
        fetch.add_argument("--market", default=None, metavar="M",
                           help="KOSPI/KOSDAQ/KONEX (only stock and stock-derivative services)")
        fetch.add_argument("--json", action="store_true", help="emit JSON instead of text")
        fetch.set_defaults(run=_run_fetch, group=group)

    list_cmd = commands.add_parser("list", help="list services (offline)")
    list_cmd.add_argument("group", nargs="?", choices=catalog.groups(), default=None,
                          help="only this group; omit for all")
    list_cmd.add_argument("--json", action="store_true", help="emit JSON instead of text")
    list_cmd.set_defaults(run=_run_list)

    fields_cmd = commands.add_parser("fields", help="a service's field schema (offline)")
    fields_cmd.add_argument("group", choices=catalog.groups(), help="accessor group")
    fields_cmd.add_argument("name", help="service method (e.g. kospi)")
    fields_cmd.add_argument("--json", action="store_true", help="emit JSON instead of text")
    fields_cmd.set_defaults(run=_run_fields)

    return parser


def _run_fetch(args: argparse.Namespace) -> int:
    method = getattr(getattr(KRX(), args.group), args.name)
    kwargs = {}
    if args.market is not None:
        if "market" in inspect.signature(method).parameters:
            kwargs["market"] = args.market
        else:
            print(f"{_ERROR_PREFIX}{args.group} {args.name} takes no --market",
                  file=sys.stderr)
            return 2
    _emit(method(args.date, **kwargs), args.json)
    return 0


def _run_list(args: argparse.Namespace) -> int:
    target = [args.group] if args.group else catalog.groups()
    if args.json:
        print(json.dumps({g: catalog.methods(g) for g in target}, ensure_ascii=False, indent=2))
        return 0
    lines = []
    for group in target:
        lines.append(group)
        lines += [f"  {group} {name}" for name in catalog.methods(group)]
    print("\n".join(lines))
    return 0


def _run_fields(args: argparse.Namespace) -> int:
    try:
        fields = catalog.fields(args.group, args.name)
    except KeyError:
        print(f"{_ERROR_PREFIX}unknown service {args.group} {args.name!r} "
              f"(try `{_PROG} list {args.group}`)", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(fields, ensure_ascii=False, indent=2))
        return 0
    print("\n".join(fields))
    return 0


def _emit(rows: Sequence[Row], as_json: bool) -> None:
    if as_json:
        print(json.dumps(list(rows), ensure_ascii=False, indent=2))
    else:
        print(_render_rows(rows))


def _render_rows(rows: Sequence[Row]) -> str:
    """Rows as an aligned table over the first row's keys (up to ``_MAX_SHOWN_ROWS``),
    then a total count. Empty -> ``(no rows)``."""
    if not rows:
        return "(no rows)"
    headers = list(rows[0].keys())
    shown = rows[:_MAX_SHOWN_ROWS]
    body = [[row.get(key, "") for key in headers] for row in shown]
    table = _render(headers, body)
    if len(rows) > len(shown):
        return f"{table}\n... ({len(rows)} rows total, showing {len(shown)})"
    return f"{table}\n({len(rows)} rows)"


def _render(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Rows as an aligned table over ``headers``, one row per line."""
    columns = list(zip(headers, *rows, strict=True)) if rows else [(h,) for h in headers]
    widths = [max(len(str(cell)) for cell in column) for column in columns]
    line = "  ".join(str(h).ljust(w) for h, w in zip(headers, widths, strict=True))
    body = "\n".join(
        "  ".join(str(cell).ljust(w) for cell, w in zip(row, widths, strict=True))
        for row in rows)
    return f"{line}\n{body}" if body else line


if __name__ == "__main__":
    raise SystemExit(main())
