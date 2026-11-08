"""Bits and bytes related humanization."""

from __future__ import annotations

__lazy_modules__ = {"humanize.i18n"}

from humanize.i18n import _gettext as _

suffixes = {
    "decimal": (
        "kB",
        "MB",
        "GB",
        "TB",
        "PB",
        "EB",
        "ZB",
        "YB",
        "RB",
        "QB",
    ),
    "binary": (
        "KiB",
        "MiB",
        "GiB",
        "TiB",
        "PiB",
        "EiB",
        "ZiB",
        "YiB",
        "RiB",
        "QiB",
    ),
    "gnu": "KMGTPEZYRQ",
}


def naturalsize(
    value: float | str,
    binary: bool = False,
    gnu: bool = False,
    format: str = "%.1f",
) -> str:
    """Format a number of bytes like a human-readable filesize (e.g. 10 kB).

    By default, decimal suffixes (kB, MB) are used.

    Non-GNU modes are compatible with jinja2's `filesizeformat` filter.

    Examples:
        ```pycon
        >>> naturalsize(3000000)
        '3.0 MB'
        >>> naturalsize(300, False, True)
        '300B'
        >>> naturalsize(3000, False, True)
        '2.9K'
        >>> naturalsize(3000, False, True, "%.3f")
        '2.930K'
        >>> naturalsize(3000, True)
        '2.9 KiB'
        >>> naturalsize(10**28)
        '10.0 RB'
        >>> naturalsize(10**34 * 3)
        '30000.0 QB'
        >>> naturalsize(-4096, True)
        '-4.0 KiB'

        ```

    Args:
        value (int, float, str): Integer to convert.
        binary (bool): If `True`, uses binary suffixes (KiB, MiB) with base
            2<sup>10</sup> instead of 10<sup>3</sup>.
        gnu (bool): If `True`, the binary argument is ignored and GNU-style
            (`ls -sh` style) prefixes are used (K, M) with the 2**10 definition.
        format (str): Custom formatter.

    Returns:
        str: Human readable representation of a filesize.
    """
    if gnu:
        suffix = suffixes["gnu"]
    elif binary:
        suffix = suffixes["binary"]
    else:
        suffix = suffixes["decimal"]

    base = 1024 if (gnu or binary) else 1000
    bytes_ = float(value)
    abs_bytes = abs(bytes_)

    if abs_bytes == 1 and not gnu:
        return _("%d Byte") % int(bytes_)

    if abs_bytes < base:
        return f"{int(bytes_)}B" if gnu else _("%d Bytes") % int(bytes_)

    from math import log

    exp = int(min(log(abs_bytes, base), len(suffix)))
    # The suffix is chosen from the unrounded byte count, but `format` rounds the
    # mantissa afterward; rounding can push it up to `base` (e.g. 999999 is
    # 999.999 kB, which formats to "1000.0 kB"). When that happens and a larger
    # suffix is available, step up one suffix so the result reads "1.0 MB".
    if exp < len(suffix) and abs(float(format % (abs_bytes / (base**exp)))) >= base:
        exp += 1
    space = "" if gnu else " "
    ret: str = format % (bytes_ / (base**exp)) + space + _(suffix[exp - 1])
    return ret


def naturalrate(
    value: float | str,
    unit: str = "B",
    per: str = "s",
    binary: bool = False,
    format: str = "%.1f",
) -> str:
    """Format a throughput rate like a human-readable size per unit of time.

    For example, `1.0 MB/s`.

    The size is formatted with `naturalsize`, so the same suffixes, rounding,
    and edge cases (zero, negative, and non-numeric input) apply.

    Examples:
        ```pycon
        >>> naturalrate(3000000)
        '3.0 MB/s'
        >>> naturalrate(3000000, per="h")
        '3.0 MB/h'
        >>> naturalrate(3000000, binary=True)
        '2.9 MiB/s'
        >>> naturalrate(-4096, per="min")
        '-4.1 kB/min'
        >>> naturalrate(10**6, unit="bit")
        '1.0 Mbit/s'

        ```

    Args:
        value (int, float, str): Rate to convert.
        unit (str): Unit of `value`; the default `"B"` is already expressed by
            the size suffix, so any other value replaces the byte unit in the
            suffix (e.g. `"bit"` gives `'1.0 Mbit/s'`).
        per (str): Unit of time the rate is measured over.
        binary (bool): If `True`, uses binary suffixes (KiB, MiB) with base
            2<sup>10</sup> instead of 10<sup>3</sup>.
        format (str): Custom formatter passed to `naturalsize`.

    Returns:
        str: Human readable representation of a rate.
    """
    size = naturalsize(value, binary=binary, format=format)
    if unit != "B":
        for ending in ("Bytes", "Byte", "B"):
            if size.endswith(ending):
                plural = "s" if ending == "Bytes" else ""
                size = f"{size[: -len(ending)]}{unit}{plural}"
                break
    return f"{size}/{per}"


def format_rate(size_str: str, per: str = "s") -> str:
    """Join a human-readable size with a time unit using a slash.

    This helper composes an already-formatted size (for example from
    ``naturalsize``) with a period label.

    Examples:
        >>> format_rate("1.0 MB")
        '1.0 MB/s'
        >>> format_rate("300 Bytes", "min")
        '300 Bytes/min'
    """
    return f"{size_str}/{per}"
