from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys

import humanize

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

    Handler = Callable[[argparse.Namespace], str]

_DELTA_UNITS = ("seconds", "milliseconds", "microseconds")
_PRECISE_UNITS = (
    "microseconds",
    "milliseconds",
    "seconds",
    "minutes",
    "hours",
    "days",
    "months",
    "years",
)


_NEGATIVE_NUMBER = re.compile(
    r"^-(?:(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?|inf|infinity|nan)$", re.IGNORECASE
)


class _ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Treat values like -1e3 and -inf as positionals, not options.
        self._negative_number_matcher = _NEGATIVE_NUMBER


def _number(text: str) -> int | float:
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        msg = f"invalid number: {text!r}"
        raise ValueError(msg) from None


def _float(text: str) -> float:
    try:
        return float(text)
    except ValueError:
        msg = f"invalid number: {text!r}"
        raise ValueError(msg) from None


def _datetime(text: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        msg = f"invalid ISO 8601 datetime: {text!r}"
        raise ValueError(msg) from None


def _date(text: str) -> dt.date | dt.datetime:
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        pass
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        msg = f"invalid ISO 8601 date: {text!r}"
        raise ValueError(msg) from None


def _time_value(text: str) -> dt.datetime | float:
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        msg = f"invalid number of seconds or ISO 8601 datetime: {text!r}"
        raise ValueError(msg) from None


def _iso_datetime_arg(text: str) -> dt.datetime:
    try:
        return _datetime(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _apnumber(args: argparse.Namespace) -> str:
    return humanize.apnumber(_number(args.value))


def _clamp(args: argparse.Namespace) -> str:
    return humanize.clamp(
        _float(args.value),
        format=args.format,
        floor=args.floor,
        ceil=args.ceil,
        floor_token=args.floor_token,
        ceil_token=args.ceil_token,
    )


def _fractional(args: argparse.Namespace) -> str:
    return humanize.fractional(_number(args.value))


def _intcomma(args: argparse.Namespace) -> str:
    return humanize.intcomma(_number(args.value), ndigits=args.ndigits)


def _intword(args: argparse.Namespace) -> str:
    return humanize.intword(_number(args.value), format=args.format)


def _metric(args: argparse.Namespace) -> str:
    return humanize.metric(_float(args.value), unit=args.unit, precision=args.precision)


def _ordinal(args: argparse.Namespace) -> str:
    return humanize.ordinal(_number(args.value), gender=args.gender)


def _scientific(args: argparse.Namespace) -> str:
    return humanize.scientific(_number(args.value), precision=args.precision)


def _naturalsize(args: argparse.Namespace) -> str:
    return humanize.naturalsize(
        _number(args.value), binary=args.binary, gnu=args.gnu, format=args.format
    )


def _natural_list(args: argparse.Namespace) -> str:
    return humanize.natural_list(args.value)


def _naturaldate(args: argparse.Namespace) -> str:
    return humanize.naturaldate(_date(args.value))


def _naturalday(args: argparse.Namespace) -> str:
    return humanize.naturalday(_date(args.value), format=args.format)


def _naturaldelta(args: argparse.Namespace) -> str:
    return humanize.naturaldelta(
        _float(args.value), months=args.months, minimum_unit=args.minimum_unit
    )


def _naturaltime(args: argparse.Namespace) -> str:
    return humanize.naturaltime(
        _time_value(args.value),
        future=args.future,
        months=args.months,
        minimum_unit=args.minimum_unit,
        when=args.when,
    )


def _precisedelta(args: argparse.Namespace) -> str:
    return humanize.precisedelta(
        _float(args.value),
        minimum_unit=args.minimum_unit,
        suppress=args.suppress,
        format=args.format,
    )


def _common_options() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--locale",
        metavar="L",
        help="locale to format in, e.g. de_DE (default: no translation)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a JSON object with the formatter, value, locale and result",
    )
    return parser


def _add_formatter(
    subparsers: argparse._SubParsersAction[_ArgumentParser],
    name: str,
    handler: Handler,
    help: str,
    value_help: str,
    *,
    many: bool = False,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name, help=help, description=help, parents=[_common_options()]
    )
    parser.add_argument("value", nargs="+" if many else None, help=value_help)
    parser.set_defaults(handler=handler)
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="humanize",
        description="Format values in a human-readable way.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {humanize.__version__}"
    )
    subparsers = parser.add_subparsers(
        dest="formatter", metavar="formatter", required=True
    )

    number = "a number, e.g. 1234567 or 0.5"
    seconds = "a number of seconds"

    _add_formatter(
        subparsers,
        "apnumber",
        _apnumber,
        "Spell out numbers 1-9 in Associated Press style.",
        number,
    )

    p = _add_formatter(
        subparsers,
        "clamp",
        _clamp,
        "Clamp a number between a floor and a ceiling.",
        number,
    )
    p.add_argument("--format", default="{:}", help="format string (default: {:})")
    p.add_argument("--floor", type=float, help="lowest value before clamping")
    p.add_argument("--ceil", type=float, help="highest value before clamping")
    p.add_argument("--floor-token", default="<", help="prefix when floored")
    p.add_argument("--ceil-token", default=">", help="prefix when ceiled")

    _add_formatter(
        subparsers,
        "fractional",
        _fractional,
        "Convert a number to a fraction.",
        number,
    )

    p = _add_formatter(
        subparsers,
        "intcomma",
        _intcomma,
        "Add thousands separators to a number.",
        number,
    )
    p.add_argument("--ndigits", type=int, help="digits to round to")

    p = _add_formatter(
        subparsers,
        "intword",
        _intword,
        "Convert a large number to a friendly word form.",
        number,
    )
    p.add_argument("--format", default="%.1f", help="format string (default: %%.1f)")

    p = _add_formatter(
        subparsers,
        "metric",
        _metric,
        "Format a number with a metric SI prefix.",
        number,
    )
    p.add_argument("--unit", default="", help="unit suffix, e.g. V or m")
    p.add_argument(
        "--precision", type=int, default=3, help="significant digits (default: 3)"
    )

    p = _add_formatter(
        subparsers,
        "ordinal",
        _ordinal,
        "Convert an integer to its ordinal.",
        number,
    )
    p.add_argument(
        "--gender",
        choices=("male", "female"),
        default="male",
        help="gender for translations (default: male)",
    )

    p = _add_formatter(
        subparsers,
        "scientific",
        _scientific,
        "Format a number in scientific notation.",
        number,
    )
    p.add_argument(
        "--precision", type=int, default=2, help="decimal places (default: 2)"
    )

    p = _add_formatter(
        subparsers,
        "naturalsize",
        _naturalsize,
        "Format a number of bytes as a file size.",
        "a number of bytes",
    )
    p.add_argument("--binary", action="store_true", help="use binary (KiB) suffixes")
    p.add_argument("--gnu", action="store_true", help="use GNU-style suffixes")
    p.add_argument("--format", default="%.1f", help="format string (default: %%.1f)")

    _add_formatter(
        subparsers,
        "natural_list",
        _natural_list,
        "Join items into a human-readable list.",
        "one or more items",
        many=True,
    )

    _add_formatter(
        subparsers,
        "naturaldate",
        _naturaldate,
        "Format a date naturally, including the year if far away.",
        "an ISO 8601 date or datetime",
    )

    p = _add_formatter(
        subparsers,
        "naturalday",
        _naturalday,
        "Format a date as today/tomorrow/yesterday or a date string.",
        "an ISO 8601 date or datetime",
    )
    p.add_argument(
        "--format", default="%b %d", help="strftime format (default: %%b %%d)"
    )

    p = _add_formatter(
        subparsers,
        "naturaldelta",
        _naturaldelta,
        "Format a time delta naturally, without tense.",
        seconds,
    )
    p.add_argument(
        "--months",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use months between days and years (default: true)",
    )
    p.add_argument(
        "--minimum-unit",
        choices=_DELTA_UNITS,
        default="seconds",
        help="lowest unit to use (default: seconds)",
    )

    p = _add_formatter(
        subparsers,
        "naturaltime",
        _naturaltime,
        "Format a time relative to now, with tense.",
        "a number of seconds or an ISO 8601 datetime",
    )
    p.add_argument(
        "--future",
        action="store_true",
        help="treat a number of seconds as future rather than past",
    )
    p.add_argument(
        "--months",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use months between days and years (default: true)",
    )
    p.add_argument(
        "--minimum-unit",
        choices=_DELTA_UNITS,
        default="seconds",
        help="lowest unit to use (default: seconds)",
    )
    p.add_argument(
        "--when",
        type=_iso_datetime_arg,
        help="ISO 8601 datetime to compare against (default: now)",
    )

    p = _add_formatter(
        subparsers,
        "precisedelta",
        _precisedelta,
        "Format a time delta precisely.",
        seconds,
    )
    p.add_argument(
        "--minimum-unit",
        choices=_PRECISE_UNITS,
        default="seconds",
        help="lowest unit to use (default: seconds)",
    )
    p.add_argument(
        "--suppress",
        action="append",
        choices=_PRECISE_UNITS,
        default=[],
        help="unit to suppress; may be repeated",
    )
    p.add_argument("--format", default="%0.2f", help="format string (default: %%0.2f)")

    return parser


def _format(args: argparse.Namespace) -> str:
    handler: Handler = args.handler
    return handler(args)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    prefix = f"{parser.prog} {args.formatter}: error:"
    try:
        if args.locale is not None:
            try:
                humanize.activate(args.locale)
            except OSError:
                print(
                    f"{prefix} locale not available: {args.locale!r}", file=sys.stderr
                )
                return 1
        try:
            result = _format(args)
        except (ArithmeticError, LookupError, TypeError, ValueError) as exc:
            print(f"{prefix} {exc}", file=sys.stderr)
            return 1
    finally:
        humanize.deactivate()
    if args.json:
        result = json.dumps(
            {
                "formatter": args.formatter,
                "value": args.value,
                "locale": args.locale,
                "result": result,
            }
        )
    print(result)
    return 0
