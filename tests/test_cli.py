"""Tests for the humanize command-line interface."""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

import humanize
from humanize import cli


@pytest.fixture(autouse=True)
def _reset_locale() -> Iterator[None]:
    yield
    humanize.deactivate()


def run(argv: list[str]) -> None:
    assert cli.main(argv) == 0


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["ordinal", "1"], "1st"),
        (["ordinal", "2", "--gender", "female"], "2nd"),
        (["intcomma", "1234567"], "1,234,567"),
        (["intcomma", "1234.5454545", "--ndigits", "2"], "1,234.55"),
        (["intword", "1200000"], "1.2 million"),
        (["apnumber", "7"], "seven"),
        (["fractional", "0.3"], "3/10"),
        (["scientific", "500"], "5.00 x 10²"),
        (["scientific", "500", "--precision", "1"], "5.0 x 10²"),
        (["clamp", "0.0001", "--floor", "0.01"], "<0.01"),
        (["clamp", "5", "--ceil", "3", "--ceil-token", "max "], "max 3.0"),
        (["metric", "1500", "--unit", "V"], "1.50 kV"),
        (["naturalsize", "3000000"], "3.0 MB"),
        (["naturalsize", "3000", "--binary"], "2.9 KiB"),
        (["naturalsize", "3000", "--gnu"], "2.9K"),
        (["naturalsize", "3000", "--format", "%.3f", "--gnu"], "2.930K"),
        (["format_rate", "1.0 MB"], "1.0 MB/s"),
        (["format_rate", "300 Bytes", "--per", "min"], "300 Bytes/min"),
        (["natural_list", "a", "b", "c"], "a, b and c"),
        (["naturaldelta", "3600"], "an hour"),
        (["naturaldelta", "P1DT2H", "--no-months"], "a day"),
        (["naturaldelta", "90", "--minimum-unit", "milliseconds"], "2 minutes"),
        (["precisedelta", "3633", "--suppress", "seconds"], "1 hour and 0.55 minutes"),
        (["precisedelta", "none"], "None"),
        (["naturaltime", "now"], "now"),
        (["naturalday", "now"], "today"),
        (["naturaldate", "2020-01-01"], "Jan 01 2020"),
        (["decimal_separator"], "."),
        (["thousands_separator"], ","),
    ],
)
def test_commands(
    capsys: pytest.CaptureFixture[str], argv: list[str], expected: str
) -> None:
    run(argv)
    assert capsys.readouterr().out.strip() == expected


def test_number_fallback_to_string(capsys: pytest.CaptureFixture[str]) -> None:
    run(["intcomma", "not-a-number"])
    assert capsys.readouterr().out.strip() == "not-a-number"


def test_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    run(["intcomma", "1000", "--json"])
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == {"command": "intcomma", "result": "1,000"}


def test_json_output_none_result(capsys: pytest.CaptureFixture[str]) -> None:
    run(["clamp", "nan", "--json"])
    out = capsys.readouterr().out.strip()
    assert json.loads(out)["command"] == "clamp"


def test_locale_option(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(cli, "activate", lambda locale: calls.append(locale))
    run(["naturaltime", "3600", "--locale", "de_DE"])
    assert calls == ["de_DE"]
    assert capsys.readouterr().out.strip() == "an hour ago"


def test_locale_option_before_subcommand(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(cli, "activate", lambda locale: calls.append(locale))
    assert cli.main(["--locale", "fr_FR", "intcomma", "1000"]) == 0
    assert calls == ["fr_FR"]
    assert capsys.readouterr().out.strip() == "1,000"


def test_naturaltime_when_now(capsys: pytest.CaptureFixture[str]) -> None:
    run(["naturaltime", "60", "--when", "now"])
    assert capsys.readouterr().out.strip() == "a minute ago"


def test_naturaltime_future_and_when(capsys: pytest.CaptureFixture[str]) -> None:
    run(["naturaltime", "3600", "--future", "--when", "2024-01-01T00:00:00"])
    assert capsys.readouterr().out.strip() == "an hour from now"


def test_naturaltime_datetime_value(capsys: pytest.CaptureFixture[str]) -> None:
    run(["naturaltime", "2024-01-01", "--when", "2024-01-02"])
    assert capsys.readouterr().out.strip() == "a day ago"


def test_naturalday_format(capsys: pytest.CaptureFixture[str]) -> None:
    run(["naturalday", "2020-06-15", "--format", "%Y"])
    assert capsys.readouterr().out.strip() == "2020"


def test_precisedelta_format(capsys: pytest.CaptureFixture[str]) -> None:
    run(["precisedelta", "90", "--minimum-unit", "minutes", "--format", "%0.1f"])
    assert capsys.readouterr().out.strip() == "1.5 minutes"


def test_months_option(capsys: pytest.CaptureFixture[str]) -> None:
    run(["naturaldelta", "P400D", "--months"])
    assert "month" in capsys.readouterr().out


def test_invalid_float(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["clamp", "abc"])


def test_invalid_float_option(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["clamp", "1", "--floor", "abc"])


def test_invalid_duration(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["naturaldelta", "P"])


def test_invalid_datetime(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["naturalday", "not-a-date"])


def test_invalid_when(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["naturaltime", "3600", "--when", "not-a-date"])


def test_no_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main([])


def test_unknown_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["bogus"])


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert "formatter" in capsys.readouterr().out


def test_module_entrypoint() -> None:
    import humanize.__main__  # noqa: F401
