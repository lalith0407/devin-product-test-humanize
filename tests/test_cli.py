"""CLI tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable

import pytest

from humanize import cli


@pytest.fixture
def run_cli(capsys: pytest.CaptureFixture[str]) -> Callable[..., str]:
    def _run(*args: str) -> str:
        assert cli.main(list(args)) == 0
        return capsys.readouterr().out.strip()

    return _run


@pytest.mark.parametrize(
    "args, expected",
    [
        (["ordinal", "3"], "3rd"),
        (["ordinal", "1", "--gender", "female"], "1st"),
        (["intcomma", "1234567"], "1,234,567"),
        (["intcomma", "1234.5", "--ndigits", "2"], "1,234.50"),
        (["intcomma", "1.5"], "1.5"),
        (["intword", "1200000"], "1.2 million"),
        (["intword", "5", "--format", "%.2f"], "5"),
        (["apnumber", "2100"], "2100"),
        (["fractional", "0.5"], "1/2"),
        (["fractional", "1.5"], "1 1/2"),
        (["scientific", "500", "--precision", "3"], "5.000 x 10²"),
        (["scientific", "foo"], "foo"),
        (["clamp", "0.001", "--floor", "0.01"], "<0.01"),
        (["clamp", "5", "--floor", "10", "--floor-token", "under_"], "under_10.0"),
        (["clamp", "0.99", "--format", "{:.0%}", "--ceil", "0.99"], "99%"),
        (["metric", "1500", "--unit", "V"], "1.50 kV"),
        (["metric", "2e8", "--unit", "W"], "200 MW"),
        (["naturalsize", "3000000"], "3.0 MB"),
        (["naturalsize", "10", "--gnu"], "10B"),
        (["naturalsize", "3000", "--binary", "--format", "%.3f"], "2.930 KiB"),
        (["format_rate", "1.0 MB", "--per", "min"], "1.0 MB/min"),
        (["natural_list", "a", "b", "c"], "a, b and c"),
        (["natural_list", "one"], "one"),
        (["naturaldelta", "61"], "a minute"),
        (["naturaldelta", "3661", "--no-months"], "an hour"),
        (["naturaldelta", "61", "--minimum-unit", "milliseconds"], "a minute"),
        (["naturaltime", "3600", "--future"], "an hour from now"),
        (["naturaltime", "0"], "now"),
        (
            [
                "naturaltime",
                "2024-06-01T00:00:00",
                "--when",
                "2024-06-01T01:00:00",
            ],
            "an hour ago",
        ),
        (["naturalday", "2024-05-01"], "May 01"),
        (["naturalday", "2024-05-01", "--format", "%Y"], "2024"),
        (["naturaldate", "2019-01-01"], "Jan 01 2019"),
        (["precisedelta", "3661.5"], "1 hour, 1 minute and 1.50 seconds"),
        (
            [
                "precisedelta",
                "90",
                "--suppress",
                "seconds",
                "--suppress",
                "milliseconds",
                "--suppress",
                "microseconds",
            ],
            "1.50 minutes",
        ),
        (
            ["precisedelta", "3661", "--minimum-unit", "minutes"],
            "1 hour and 1.02 minutes",
        ),
        (["decimal_separator"], "."),
        (["thousands_separator"], ","),
    ],
)
def test_commands(run_cli: Callable[..., str], args: list[str], expected: str) -> None:
    assert run_cli(*args) == expected


def test_json_output(run_cli: Callable[..., str]) -> None:
    output = run_cli("intcomma", "1234", "--json")
    assert json.loads(output) == {"command": "intcomma", "result": "1,234"}


def test_json_output_unicode(run_cli: Callable[..., str]) -> None:
    output = run_cli("scientific", "500", "--json")
    assert json.loads(output)["result"] == "5.00 x 10²"


def test_locale_activates_and_deactivates_for_the_call(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        cli, "activate", lambda locale: calls.append(("activate", locale))
    )
    monkeypatch.setattr(cli, "deactivate", lambda: calls.append(("deactivate", None)))
    assert cli.main(["intcomma", "1234", "--locale", "en_US"]) == 0
    assert capsys.readouterr().out.strip() == "1,234"
    assert calls == [("activate", "en_US"), ("deactivate", None)]


def test_locale_en_us_outputs_default_separators(
    run_cli: Callable[..., str],
) -> None:
    assert run_cli("decimal_separator", "--locale", "en_US") == "."
    assert run_cli("thousands_separator", "--locale", "en_US") == ","


@pytest.mark.parametrize(
    "args",
    [
        ["intcomma"],
        ["intcomma", "1", "--bogus"],
        ["naturalday", "not-a-date"],
        ["naturaltime", "not-a-date-or-number"],
        ["naturaldelta", "10", "--minimum-unit", "days"],
        ["precisedelta", "10", "--minimum-unit", "fortnights"],
        ["natural_list"],
        ["unknown-command", "1"],
    ],
)
def test_invalid_arguments_exit_with_error(args: list[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(args)
    assert exc_info.value.code == 2


def test_module_entrypoint() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "humanize", "intcomma", "1234"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "1,234"


def test_console_script() -> None:
    executable = shutil.which("humanize")
    if executable is None:
        pytest.skip("humanize console script is not installed")
    result = subprocess.run(
        [executable, "intcomma", "1234"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "1,234"
