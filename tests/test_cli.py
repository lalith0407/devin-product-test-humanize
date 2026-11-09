from __future__ import annotations

import argparse
import subprocess
import sys

import freezegun
import pytest

import humanize
from humanize import cli


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = cli.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


@pytest.mark.parametrize(
    "argv, expected",
    [
        (["apnumber", "5"], "five"),
        (["apnumber", "10"], "10"),
        (["clamp", "0.0001", "--floor", "0.01", "--format", "{:.0%}"], "<1%"),
        (["clamp", "0.999", "--ceil", "0.99", "--format", "{:.0%}"], ">99%"),
        (
            [
                "clamp",
                "0.0001",
                "--floor",
                "0.01",
                "--format",
                "{:.0%}",
                "--floor-token",
                "under ",
            ],
            "under 1%",
        ),
        (
            [
                "clamp",
                "0.999",
                "--ceil",
                "0.99",
                "--format",
                "{:.0%}",
                "--ceil-token",
                "over ",
            ],
            "over 99%",
        ),
        (["fractional", "0.3"], "3/10"),
        (["fractional", "1.5"], "1 1/2"),
        (["intcomma", "1234567"], "1,234,567"),
        (["intcomma", "1234.5454545", "--ndigits", "2"], "1,234.55"),
        (["intcomma", "-1000"], "-1,000"),
        (["intword", "1200000000"], "1.2 billion"),
        (["intword", "1200000000", "--format", "%.2f"], "1.20 billion"),
        (["metric", "1500", "--unit", "V"], "1.50 kV"),
        (["metric", "1500", "--unit", "V", "--precision", "2"], "1.5 kV"),
        (["ordinal", "3"], "3rd"),
        (["ordinal", "3", "--gender", "female"], "3rd"),
        (["scientific", "500"], "5.00 x 10²"),
        (["scientific", "500", "--precision", "1"], "5.0 x 10²"),
        (["naturalsize", "3000000"], "3.0 MB"),
        (["naturalsize", "3000000", "--binary"], "2.9 MiB"),
        (["naturalsize", "3000000", "--gnu"], "2.9M"),
        (["naturalsize", "3000000", "--format", "%.3f"], "3.000 MB"),
        (["natural_list", "one"], "one"),
        (["natural_list", "one", "two", "three"], "one, two and three"),
        (["naturaldelta", "3600"], "an hour"),
        (["naturaldelta", "0.5", "--minimum-unit", "milliseconds"], "500 milliseconds"),
        (["naturaldelta", "3456000"], "a month"),
        (["naturaldelta", "3456000", "--no-months"], "40 days"),
        (["naturaltime", "3600"], "an hour ago"),
        (["naturaltime", "3600", "--future"], "an hour from now"),
        (["naturaltime", "3456000", "--no-months"], "40 days ago"),
        (
            [
                "naturaltime",
                "2020-01-01T00:00:00.500",
                "--when",
                "2020-01-01T00:00:01",
                "--minimum-unit",
                "milliseconds",
            ],
            "500 milliseconds ago",
        ),
        (
            ["naturaltime", "2020-01-01T00:00:00", "--when", "2020-01-01T02:00:00"],
            "2 hours ago",
        ),
        (["precisedelta", "3633"], "1 hour and 33 seconds"),
        (
            [
                "precisedelta",
                "3633",
                "--suppress",
                "hours",
                "--minimum-unit",
                "minutes",
            ],
            "60.55 minutes",
        ),
        (
            ["precisedelta", "3633", "--format", "%0.0f", "--minimum-unit", "hours"],
            "1 hour",
        ),
    ],
)
def test_formatters(
    capsys: pytest.CaptureFixture[str], argv: list[str], expected: str
) -> None:
    code, out, err = run(capsys, *argv)
    assert (code, out, err) == (0, expected + "\n", "")


@freezegun.freeze_time("2020-06-15 12:00:00")
@pytest.mark.parametrize(
    "argv, expected",
    [
        (["naturalday", "2020-06-15"], "today"),
        (["naturalday", "2020-06-16"], "tomorrow"),
        (["naturalday", "2020-06-14"], "yesterday"),
        (["naturalday", "2020-01-02"], "Jan 02"),
        (["naturalday", "2020-01-02", "--format", "%d/%m"], "02/01"),
        (["naturalday", "2020-06-15T08:30:00"], "today"),
        (["naturaldate", "2020-06-15"], "today"),
        (["naturaldate", "2018-01-02"], "Jan 02 2018"),
        (["naturaldate", "2020-06-15 08:30:00"], "today"),
        (["naturaltime", "2020-06-15T11:00:00"], "an hour ago"),
        (["naturaltime", "2020-06-15T13:00:00"], "an hour from now"),
    ],
)
def test_date_formatters(
    capsys: pytest.CaptureFixture[str], argv: list[str], expected: str
) -> None:
    code, out, err = run(capsys, *argv)
    assert (code, out, err) == (0, expected + "\n", "")


@pytest.mark.parametrize(
    "argv, message",
    [
        (["apnumber", "five"], "invalid number: 'five'"),
        (["clamp", "x"], "invalid number: 'x'"),
        (["intcomma", "abc"], "invalid number: 'abc'"),
        (["metric", "abc"], "invalid number: 'abc'"),
        (["naturaldate", "not-a-date"], "invalid ISO 8601 date: 'not-a-date'"),
        (["naturalday", "2020-13-01"], "invalid ISO 8601 date: '2020-13-01'"),
        (["naturaldelta", "soon"], "invalid number: 'soon'"),
        (
            ["naturaltime", "soon"],
            "invalid number of seconds or ISO 8601 datetime: 'soon'",
        ),
        (["precisedelta", "x"], "invalid number: 'x'"),
        (["naturaldelta", "1e30"], ""),
    ],
)
def test_bad_value(
    capsys: pytest.CaptureFixture[str], argv: list[str], message: str
) -> None:
    code, out, err = run(capsys, *argv)
    assert code == 1
    assert out == ""
    assert err.startswith(f"humanize {argv[0]}: error: {message}")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["nosuchformatter", "1"],
        ["intcomma"],
        ["intcomma", "1", "--ndigits", "x"],
        ["ordinal", "1", "--gender", "other"],
        ["naturaltime", "1", "--when", "yesterday"],
        ["precisedelta", "1", "--suppress", "fortnights"],
        ["natural_list"],
    ],
)
def test_usage_error(capsys: pytest.CaptureFixture[str], argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(argv)
    assert exc_info.value.code == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert "usage: humanize" in err


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"humanize {humanize.__version__}\n"


def test_help_lists_every_formatter(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    for name in FORMATTERS:
        assert name in out


FORMATTERS = sorted(
    set(humanize.__all__)
    - {"__version__", "activate", "deactivate", "decimal_separator"}
    - {"thousands_separator"}
)


def test_subcommands_match_public_formatters() -> None:
    parser = cli.build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert sorted(subparsers.choices) == FORMATTERS


def test_main_uses_sys_argv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["humanize", "intcomma", "1000"])
    assert cli.main() == 0
    assert capsys.readouterr().out == "1,000\n"


def test_python_m_humanize() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "humanize", "intcomma", "1234567"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "1,234,567"
    assert proc.stderr == ""
