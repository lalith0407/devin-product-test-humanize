"""Command-line interface for humanize."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import humanize
from humanize.filesize import format_rate
from humanize.i18n import activate, deactivate, decimal_separator, thousands_separator
from humanize.time import Unit

TYPE_CHECKING = False
if TYPE_CHECKING:
    import datetime as dt

_FINE_UNITS = ("seconds", "milliseconds", "microseconds")
_ALL_UNITS = tuple(unit.name.lower() for unit in Unit)
_RESERVED_KEYS = frozenset({"command", "locale", "json"})


def _number(value: str) -> int | float | str:
    """Parse a CLI argument as an int, a float, or fall back to a string."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _date_or_datetime(value: str) -> dt.date | dt.datetime:
    """Parse an ISO 8601 date or datetime CLI argument."""
    import datetime as dt

    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        pass
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        msg = f"invalid ISO 8601 date or datetime: {value!r}"
        raise argparse.ArgumentTypeError(msg) from exc


def _moment(value: str) -> dt.date | dt.datetime | float:
    """Parse a CLI argument as a date/datetime or a number of seconds."""
    try:
        return _date_or_datetime(value)
    except argparse.ArgumentTypeError:
        pass
    try:
        return float(value)
    except ValueError as exc:
        msg = f"invalid date, datetime or number of seconds: {value!r}"
        raise argparse.ArgumentTypeError(msg) from exc


def _default_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        key: value
        for key, value in vars(args).items()
        if not key.startswith("_") and key not in _RESERVED_KEYS
    }


def _precisedelta_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs = _default_kwargs(args)
    kwargs["suppress"] = kwargs["suppress"] or []
    return kwargs


@dataclass(frozen=True)
class _Command:
    """Specification for a single CLI subcommand."""

    name: str
    func: Callable[..., Any]
    help: str
    positional: tuple[str, dict[str, Any]] | None = None
    options: tuple[tuple[tuple[str, ...], dict[str, Any]], ...] = ()
    convert: Callable[[argparse.Namespace], dict[str, Any]] | None = None


def _time_delta_options() -> tuple[tuple[tuple[str, ...], dict[str, Any]], ...]:
    return (
        (("--minimum-unit",), {"choices": _FINE_UNITS, "default": "seconds"}),
        (("--no-months",), {"action": "store_false", "dest": "months"}),
    )


_COMMANDS: tuple[_Command, ...] = (
    _Command(
        "ordinal",
        humanize.ordinal,
        "Format an ordinal number (e.g. 1st, 2nd).",
        ("value", {"type": _number}),
        ((("--gender",), {"default": "male"}),),
    ),
    _Command(
        "intcomma",
        humanize.intcomma,
        "Format a number with thousands separators.",
        ("value", {"type": _number}),
        ((("--ndigits",), {"type": int}),),
    ),
    _Command(
        "intword",
        humanize.intword,
        "Format a number as a word (e.g. 1.0 million).",
        ("value", {"type": _number}),
        ((("--format",), {"default": "%.1f"}),),
    ),
    _Command(
        "apnumber",
        humanize.apnumber,
        "Format a number the way it appears in Associated Press style.",
        ("value", {"type": _number}),
    ),
    _Command(
        "fractional",
        humanize.fractional,
        "Format a number as a fraction.",
        ("value", {"type": _number}),
    ),
    _Command(
        "scientific",
        humanize.scientific,
        "Format a number in scientific notation.",
        ("value", {"type": _number}),
        ((("--precision",), {"type": int, "default": 2}),),
    ),
    _Command(
        "clamp",
        humanize.clamp,
        "Format a number clamped between a floor and a ceiling.",
        ("value", {"type": float}),
        (
            (("--format",), {"default": "{:}"}),
            (("--floor",), {"type": float}),
            (("--ceil",), {"type": float}),
            (("--floor-token",), {"default": "<"}),
            (("--ceil-token",), {"default": ">"}),
        ),
    ),
    _Command(
        "metric",
        humanize.metric,
        "Format a number with a metric SI unit prefix.",
        ("value", {"type": float}),
        (
            (("--unit",), {"default": ""}),
            (("--precision",), {"type": int, "default": 3}),
        ),
    ),
    _Command(
        "naturalsize",
        humanize.naturalsize,
        "Format a number of bytes as a human-readable file size.",
        ("value", {"type": _number}),
        (
            (("--binary",), {"action": "store_true"}),
            (("--gnu",), {"action": "store_true"}),
            (("--format",), {"default": "%.1f"}),
        ),
    ),
    _Command(
        "format_rate",
        format_rate,
        "Join a human-readable size with a time unit.",
        ("size_str", {"type": str}),
        ((("--per",), {"default": "s"}),),
    ),
    _Command(
        "natural_list",
        humanize.natural_list,
        "Join items into a natural-language list.",
        ("items", {"type": str, "nargs": "+"}),
    ),
    _Command(
        "naturaldelta",
        humanize.naturaldelta,
        "Format a number of seconds as a natural time delta.",
        ("value", {"type": float}),
        _time_delta_options(),
    ),
    _Command(
        "naturaltime",
        humanize.naturaltime,
        "Format a date, datetime or number of seconds as a natural time.",
        ("value", {"type": _moment}),
        (
            (("--future",), {"action": "store_true"}),
            *_time_delta_options(),
            (("--when",), {"type": _date_or_datetime}),
        ),
    ),
    _Command(
        "naturalday",
        humanize.naturalday,
        "Format a date as a natural day (e.g. 'May 1').",
        ("value", {"type": _date_or_datetime}),
        ((("--format",), {"default": "%b %d"}),),
    ),
    _Command(
        "naturaldate",
        humanize.naturaldate,
        "Format a date as a natural date, appending the year if needed.",
        ("value", {"type": _date_or_datetime}),
    ),
    _Command(
        "precisedelta",
        humanize.precisedelta,
        "Format a number of seconds as a precise time delta.",
        ("value", {"type": float}),
        (
            (
                ("--minimum-unit",),
                {"choices": _ALL_UNITS, "default": "seconds"},
            ),
            (("--suppress",), {"action": "append"}),
            (("--format",), {"default": "%0.2f"}),
        ),
        _precisedelta_kwargs,
    ),
    _Command(
        "decimal_separator",
        decimal_separator,
        "Print the decimal separator for the active locale.",
    ),
    _Command(
        "thousands_separator",
        thousands_separator,
        "Print the thousands separator for the active locale.",
    ),
)


def _common_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--locale",
        metavar="LOCALE",
        help="Locale to use for this call only (e.g. 'fr_FR')",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the result as JSON",
    )
    return parser


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="humanize",
        description="Format numbers, dates, sizes and lists for humans.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    common = _common_parser()
    for command in _COMMANDS:
        subparser = subparsers.add_parser(
            command.name, help=command.help, parents=[common]
        )
        if command.positional is not None:
            dest, kwargs = command.positional
            subparser.add_argument(dest, **kwargs)
        for flags, kwargs in command.options:
            subparser.add_argument(*flags, **kwargs)
        subparser.set_defaults(_command=command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the humanize command-line interface.

    Args:
        argv: Argument list to parse; defaults to ``sys.argv[1:]``.

    Returns:
        int: Process exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    command: _Command = args._command
    convert = command.convert or _default_kwargs
    if args.locale is not None:
        activate(args.locale)
    try:
        result = command.func(**convert(args))
    finally:
        if args.locale is not None:
            deactivate()
    if args.json:
        print(
            json.dumps({"command": command.name, "result": result}, ensure_ascii=False)
        )
    else:
        print(result)
    return 0
