"""Command-line interface for humanize.

Exposes every public formatter as a subcommand::

    python -m humanize intcomma 1234567
    python -m humanize naturaltime 2024-01-01 --locale de_DE --json
    humanize metric 1500 --unit V
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections.abc import Callable, Sequence
from typing import Any

from humanize import (
    activate,
    apnumber,
    clamp,
    decimal_separator,
    fractional,
    intcomma,
    intword,
    metric,
    natural_list,
    naturaldate,
    naturalday,
    naturaldelta,
    naturaltime,
    ordinal,
    precisedelta,
    scientific,
    thousands_separator,
)
from humanize.filesize import format_rate, naturalsize

NumberOrString = int | float | str
TimeValue = int | float | str | dt.datetime | dt.timedelta | None

MINIMUM_UNITS = (
    "microseconds",
    "milliseconds",
    "seconds",
    "minutes",
    "hours",
    "days",
    "months",
    "years",
)

# naturaldelta/naturaltime only support units of seconds or smaller.
SUBSECOND_UNITS = ("microseconds", "milliseconds", "seconds")

_DURATION_RE = re.compile(
    r"^P"
    r"(?:(?P<years>\d+(?:\.\d+)?)Y)?"
    r"(?:(?P<months>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<weeks>\d+(?:\.\d+)?)W)?"
    r"(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T"
    r"(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?"
    r")?$"
)


def _parse_number(text: str) -> NumberOrString:
    """Parse text as an int, float, or fall back to the raw string."""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def _parse_float(text: str) -> float:
    """Parse text as a float, accepting nan/inf."""
    try:
        return float(text)
    except ValueError as exc:
        msg = f"invalid float value: {text!r}"
        raise argparse.ArgumentTypeError(msg) from exc


def _parse_duration(text: str) -> dt.timedelta:
    """Parse an ISO 8601 duration such as ``P1DT2H30M`` into a timedelta."""
    match = _DURATION_RE.fullmatch(text)
    if match is None or not any(match.groupdict().values()):
        msg = f"invalid duration: {text!r} (expected seconds or ISO 8601, e.g. P1DT2H)"
        raise argparse.ArgumentTypeError(msg)
    parts = {key: float(value) for key, value in match.groupdict().items() if value}
    seconds = (
        parts.get("years", 0) * 365 * 86400
        + parts.get("months", 0) * 30.5 * 86400
        + parts.get("weeks", 0) * 7 * 86400
        + parts.get("days", 0) * 86400
        + parts.get("hours", 0) * 3600
        + parts.get("minutes", 0) * 60
        + parts.get("seconds", 0)
    )
    return dt.timedelta(seconds=seconds)


def _parse_datetime(text: str) -> dt.datetime | dt.date:
    """Parse an ISO 8601 date or datetime, or the word ``now``."""
    if text.lower() == "now":
        return dt.datetime.now()
    for parser in (dt.datetime.fromisoformat, dt.date.fromisoformat):
        try:
            return parser(text)
        except ValueError:
            continue
    msg = f"invalid date/datetime: {text!r} (expected ISO 8601 or 'now')"
    raise argparse.ArgumentTypeError(msg)


def _parse_time_value(text: str) -> TimeValue:
    """Parse a value for the time formatters.

    Accepts a number of seconds, an ISO 8601 duration, an ISO 8601
    date/datetime, ``now``, or ``none``.
    """
    if text.lower() in ("none", "null"):
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return _parse_duration(text)
    except argparse.ArgumentTypeError:
        pass
    if text.lower() == "now":
        return dt.datetime.now()
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError as exc:
        msg = (
            f"invalid time value: {text!r} (expected seconds, an ISO 8601 "
            "duration, or an ISO 8601 date/datetime)"
        )
        raise argparse.ArgumentTypeError(msg) from exc


def _parse_when(text: str) -> dt.datetime:
    """Parse the ``--when`` argument for naturaltime."""
    if text.lower() == "now":
        return dt.datetime.now()
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError as exc:
        msg = f"invalid datetime: {text!r} (expected ISO 8601 or 'now')"
        raise argparse.ArgumentTypeError(msg) from exc


def _format_result(result: Any, as_json: bool, command: str) -> str:
    """Render a formatter result as plain text or JSON."""
    if as_json:
        return json.dumps({"command": command, "result": result})
    return str(result)


def _add_common_options(
    parser: argparse.ArgumentParser, *, suppress_defaults: bool = False
) -> None:
    """Add --locale and --json options to a parser.

    With ``suppress_defaults`` the options only set the attribute when
    explicitly given, so subparser-level options do not clobber values
    already parsed by the top-level parser.
    """
    locale_default: Any = argparse.SUPPRESS if suppress_defaults else None
    json_default: Any = argparse.SUPPRESS if suppress_defaults else False
    parser.add_argument(
        "--locale",
        default=locale_default,
        metavar="LOCALE",
        help="activate a locale, e.g. de_DE or fr_FR",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=json_default,
        help="output the result as JSON",
    )


def _add_months_option(parser: argparse.ArgumentParser) -> None:
    """Add the --months/--no-months option shared by the delta formatters."""
    parser.add_argument(
        "--months",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use months for fuzziness between years",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="humanize",
        description="Format values into human-readable text.",
    )
    _add_common_options(parser)
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="formatter"
    )

    common = argparse.ArgumentParser(add_help=False)
    _add_common_options(common, suppress_defaults=True)

    def subcommand(
        name: str,
        help_text: str,
        handler: Callable[[argparse.Namespace], Any],
    ) -> argparse.ArgumentParser:
        sp = subparsers.add_parser(name, help=help_text, parents=[common])
        sp.set_defaults(handler=handler)
        return sp

    sp = subcommand(
        "ordinal",
        "Ordinal of a number, e.g. 1 -> '1st'",
        lambda a: ordinal(a.value, gender=a.gender),
    )
    sp.add_argument("value", type=_parse_number)
    sp.add_argument("--gender", choices=("male", "female"), default="male")

    sp = subcommand(
        "intcomma",
        "Integer with thousands separators, e.g. 1234567 -> '1,234,567'",
        lambda a: intcomma(a.value, ndigits=a.ndigits),
    )
    sp.add_argument("value", type=_parse_number)
    sp.add_argument("--ndigits", type=int, default=None)

    sp = subcommand(
        "intword",
        "Large number in words, e.g. 1200000 -> '1.2 million'",
        lambda a: intword(a.value, format=a.format),
    )
    sp.add_argument("value", type=_parse_number)
    sp.add_argument("--format", default="%.1f")

    sp = subcommand(
        "apnumber",
        "Associated Press style number, e.g. 7 -> 'seven'",
        lambda a: apnumber(a.value),
    )
    sp.add_argument("value", type=_parse_number)

    sp = subcommand(
        "fractional",
        "Fractional representation, e.g. 0.3 -> '3/10'",
        lambda a: fractional(a.value),
    )
    sp.add_argument("value", type=_parse_number)

    sp = subcommand(
        "scientific",
        "Scientific notation, e.g. 500 -> '5.00 x 10²'",
        lambda a: scientific(a.value, precision=a.precision),
    )
    sp.add_argument("value", type=_parse_number)
    sp.add_argument("--precision", type=int, default=2)

    sp = subcommand(
        "clamp",
        "Number clamped between floor and ceil",
        lambda a: clamp(
            a.value,
            format=a.format,
            floor=a.floor,
            ceil=a.ceil,
            floor_token=a.floor_token,
            ceil_token=a.ceil_token,
        ),
    )
    sp.add_argument("value", type=_parse_float)
    sp.add_argument("--format", default="{:}")
    sp.add_argument("--floor", type=_parse_float, default=None)
    sp.add_argument("--ceil", type=_parse_float, default=None)
    sp.add_argument("--floor-token", default="<")
    sp.add_argument("--ceil-token", default=">")

    sp = subcommand(
        "metric",
        "Value with metric SI prefix, e.g. '1500 V' -> '1.50 kV'",
        lambda a: metric(a.value, unit=a.unit, precision=a.precision),
    )
    sp.add_argument("value", type=_parse_float)
    sp.add_argument("--unit", default="")
    sp.add_argument("--precision", type=int, default=3)

    sp = subcommand(
        "naturalsize",
        "Bytes as a human-readable size, e.g. 3000000 -> '3.0 MB'",
        lambda a: naturalsize(a.value, binary=a.binary, gnu=a.gnu, format=a.format),
    )
    sp.add_argument("value", type=_parse_number)
    sp.add_argument(
        "--binary",
        action="store_true",
        help="use binary (KiB, MiB) suffixes",
    )
    sp.add_argument(
        "--gnu",
        action="store_true",
        help="use GNU-style (K, M) suffixes",
    )
    sp.add_argument("--format", default="%.1f")

    sp = subcommand(
        "format_rate",
        "Join a size string with a time unit, e.g. '1.0 MB' -> '1.0 MB/s'",
        lambda a: format_rate(a.size_str, per=a.per),
    )
    sp.add_argument("size_str")
    sp.add_argument("--per", default="s")

    sp = subcommand(
        "natural_list",
        "Join items into a natural-language list",
        lambda a: natural_list(a.items),
    )
    sp.add_argument("items", nargs="+")

    sp = subcommand(
        "naturaldelta",
        "Natural representation of a timedelta or seconds",
        lambda a: naturaldelta(a.value, months=a.months, minimum_unit=a.minimum_unit),
    )
    sp.add_argument("value", type=_parse_time_value)
    _add_months_option(sp)
    sp.add_argument("--minimum-unit", choices=SUBSECOND_UNITS, default="seconds")

    sp = subcommand(
        "naturaltime",
        "Natural representation of a datetime, timedelta, or seconds",
        lambda a: naturaltime(
            a.value,
            future=a.future,
            months=a.months,
            minimum_unit=a.minimum_unit,
            when=a.when,
        ),
    )
    sp.add_argument("value", type=_parse_time_value)
    sp.add_argument("--future", action="store_true", help="interpret numbers as future")
    _add_months_option(sp)
    sp.add_argument("--minimum-unit", choices=SUBSECOND_UNITS, default="seconds")
    sp.add_argument(
        "--when",
        type=_parse_when,
        default=None,
        help="reference datetime (ISO 8601 or 'now')",
    )

    sp = subcommand(
        "naturalday",
        "Natural day ('today', 'yesterday', ...) for a date",
        lambda a: naturalday(a.value, format=a.format),
    )
    sp.add_argument("value", type=_parse_datetime)
    sp.add_argument("--format", default="%b %d")

    sp = subcommand(
        "naturaldate",
        "Natural date, appending a year for distant dates",
        lambda a: naturaldate(a.value),
    )
    sp.add_argument("value", type=_parse_datetime)

    sp = subcommand(
        "precisedelta",
        "Precise representation of a timedelta or seconds",
        lambda a: precisedelta(
            a.value,
            minimum_unit=a.minimum_unit,
            suppress=a.suppress,
            format=a.format,
        ),
    )
    sp.add_argument("value", type=_parse_time_value)
    sp.add_argument("--minimum-unit", choices=MINIMUM_UNITS, default="seconds")
    sp.add_argument(
        "--suppress",
        nargs="*",
        default=[],
        choices=MINIMUM_UNITS,
        metavar="UNIT",
        help="units to suppress",
    )
    sp.add_argument("--format", default="%0.2f")

    subcommand(
        "decimal_separator",
        "Decimal separator for the active locale",
        lambda a: decimal_separator(),
    )
    subcommand(
        "thousands_separator",
        "Thousands separator for the active locale",
        lambda a: thousands_separator(),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``humanize`` command.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code (0 on success).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.locale is not None:
        activate(args.locale)

    result = args.handler(args)
    print(_format_result(result, args.json, args.command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
