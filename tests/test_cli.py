from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import freezegun
import pytest

import humanize
from humanize import cli

LOCALE_DIR = Path(humanize.i18n.__file__).parent / "locale"


def require_locale(locale: str) -> None:
    if not (LOCALE_DIR / locale / "LC_MESSAGES" / "humanize.mo").exists():
        pytest.skip("Generate .mo with scripts/generate-translation-binaries.sh")


@pytest.fixture(autouse=True)
def no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTHON_COLORS", "0")
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)


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
        (["intcomma", "-1e3"], "-1,000.0"),
        (["intcomma", "-.5"], "-0.5"),
        (["intcomma", "-inf"], "-Inf"),
        (["naturaltime", "-3600"], "an hour ago"),
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
        (["clamp", "1", "--format", "{foo}"], "'foo'"),
        (["clamp", "1", "--format", "{1}"], "Replacement index 1"),
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


@pytest.mark.parametrize(
    "argv, expected",
    [
        (["intcomma", "1234567", "--locale", "de_DE"], "1.234.567"),
        (["intcomma", "1234567.25", "--locale", "fr_FR"], "1 234 567,25"),
        (["intword", "1200000000", "--locale", "de_DE"], "1,2 Milliarden"),
        (["ordinal", "3", "--locale", "fr_FR", "--gender", "female"], "3e"),
        (["naturaldelta", "3600", "--locale", "ru_RU"], "час"),
        (
            ["precisedelta", "3700", "--locale", "fr_FR"],
            "1 heure, 1 minute et 40 secondes",
        ),
        (["apnumber", "5", "--locale", "de_DE"], "fünf"),
        (["intcomma", "--locale", "it_IT", "1000000"], "1.000.000"),
    ],
)
def test_locale(
    capsys: pytest.CaptureFixture[str], argv: list[str], expected: str
) -> None:
    require_locale(argv[argv.index("--locale") + 1])
    code, out, err = run(capsys, *argv)
    assert (code, out, err) == (0, f"{expected}\n", "")
    assert humanize.intcomma(1234567) == "1,234,567"
    assert humanize.apnumber(5) == "five"


@pytest.mark.parametrize("locale", ["en_US", "en_GB"])
def test_english_locale_needs_no_translations(
    capsys: pytest.CaptureFixture[str], locale: str
) -> None:
    assert run(capsys, "ordinal", "3", "--locale", locale) == (0, "3rd\n", "")


def test_locale_deactivated_after_bad_value(capsys: pytest.CaptureFixture[str]) -> None:
    require_locale("de_DE")
    code, out, err = run(capsys, "intcomma", "abc", "--locale", "de_DE")
    assert code == 1
    assert out == ""
    assert err == "humanize intcomma: error: invalid number: 'abc'\n"
    assert humanize.intcomma(1234567) == "1,234,567"


def test_locale_replaces_previously_active_locale(
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_locale("de_DE")
    require_locale("fr_FR")
    humanize.activate("fr_FR")
    try:
        assert run(capsys, "apnumber", "5", "--locale", "de_DE") == (0, "fünf\n", "")
    finally:
        humanize.deactivate()
    assert humanize.apnumber(5) == "five"


@pytest.mark.parametrize("locale", ["xx_XX", "not-a-locale"])
def test_unavailable_locale(capsys: pytest.CaptureFixture[str], locale: str) -> None:
    code, out, err = run(capsys, "intcomma", "1000", "--locale", locale, "--json")
    assert code == 1
    assert out == ""
    assert err == f"humanize intcomma: error: locale not available: {locale!r}\n"
    assert humanize.intcomma(1000) == "1,000"


@pytest.mark.parametrize(
    "argv, value, locale, result",
    [
        (["intcomma", "1234567", "--json"], "1234567", None, "1,234,567"),
        (["ordinal", "2", "--json"], "2", None, "2nd"),
        (
            ["natural_list", "a", "b", "c", "--json"],
            ["a", "b", "c"],
            None,
            "a, b and c",
        ),
        (["natural_list", "--json", "x"], ["x"], None, "x"),
        (["naturalsize", "--json", "--binary", "1024"], "1024", None, "1.0 KiB"),
        (["ordinal", "3", "--json", "--locale", "en_GB"], "3", "en_GB", "3rd"),
    ],
)
def test_json(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    value: str | list[str],
    locale: str | None,
    result: str,
) -> None:
    code, out, err = run(capsys, *argv)
    assert code == 0
    assert err == ""
    assert out.endswith("\n")
    assert out.count("\n") == 1
    assert json.loads(out) == {
        "formatter": argv[0],
        "value": value,
        "locale": locale,
        "result": result,
    }


def test_json_with_locale(capsys: pytest.CaptureFixture[str]) -> None:
    require_locale("de_DE")
    code, out, err = run(capsys, "intcomma", "1234567", "--locale", "de_DE", "--json")
    assert (code, err) == (0, "")
    assert json.loads(out) == {
        "formatter": "intcomma",
        "value": "1234567",
        "locale": "de_DE",
        "result": "1.234.567",
    }


def test_json_bad_value(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(capsys, "intcomma", "abc", "--json")
    assert code == 1
    assert out == ""
    assert err == "humanize intcomma: error: invalid number: 'abc'\n"


SAMPLE_VALUES = {
    "naturaldate": "2020-02-02",
    "naturalday": "2020-02-02",
}


@pytest.mark.parametrize("name", FORMATTERS)
def test_every_formatter_accepts_json_and_locale(
    capsys: pytest.CaptureFixture[str], name: str
) -> None:
    value = SAMPLE_VALUES.get(name, "1")
    code, out, err = run(capsys, name, value, "--locale", "en_US", "--json")
    assert (code, err) == (0, "")
    data = json.loads(out)
    assert data["formatter"] == name
    assert data["value"] == ([value] if name == "natural_list" else value)
    assert data["locale"] == "en_US"
    assert isinstance(data["result"], str)


def test_json_flag_defaults() -> None:
    args = cli.build_parser().parse_args(["intcomma", "1"])
    assert args.json is False
    assert args.locale is None


def test_python_m_humanize_json_locale() -> None:
    require_locale("de_DE")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "humanize",
            "intcomma",
            "1234567",
            "--locale",
            "de_DE",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stderr == ""
    assert json.loads(proc.stdout) == {
        "formatter": "intcomma",
        "value": "1234567",
        "locale": "de_DE",
        "result": "1.234.567",
    }
