# Command-line interface

humanize ships a command-line interface exposing every public formatter as a
subcommand. It can be run as a module or via the `humanize` console script
(installed with the package):

```console
$ python -m humanize intcomma 1234567
1,234,567
$ humanize metric 1500 --unit V
1.50 kV
```

## Usage

```text
humanize [-h] [--locale LOCALE] [--json] formatter ...
```

The global options may be given either before or after the subcommand:

- `--locale LOCALE` — activate a locale (e.g. `de_DE`, `fr_FR`) before
  formatting. See [Internationalisation](i18n.md).
- `--json` — wrap the result in a JSON object:
  `{"command": "intcomma", "result": "1,000"}`.

## Subcommands

Each subcommand mirrors the signature of the corresponding Python function.
Arguments that are numbers are parsed as `int` or `float` when possible and
otherwise passed through as strings, matching the `NumberOrString` parameters
of the library.

### Number formatters

| Subcommand | Arguments | Description |
| --- | --- | --- |
| `ordinal` | `value [--gender male\|female]` | Ordinal, e.g. `1` → `1st` |
| `intcomma` | `value [--ndigits N]` | Thousands separators |
| `intword` | `value [--format FMT]` | Large numbers in words |
| `apnumber` | `value` | Associated Press style |
| `fractional` | `value` | Fractional representation |
| `scientific` | `value [--precision N]` | Scientific notation |
| `clamp` | `value [--format] [--floor] [--ceil] [--floor-token] [--ceil-token]` | Clamped number |
| `metric` | `value [--unit U] [--precision N]` | Metric SI prefix |

### Filesize formatters

| Subcommand | Arguments | Description |
| --- | --- | --- |
| `naturalsize` | `value [--binary] [--gnu] [--format FMT]` | Human-readable size |
| `format_rate` | `size_str [--per UNIT]` | Size per time unit |

### List formatters

| Subcommand | Arguments | Description |
| --- | --- | --- |
| `natural_list` | `items...` | Natural-language list |

### Time formatters

The time formatters accept several value formats for `value`:

- a number of seconds (`3600`, `-90.5`)
- an ISO 8601 duration (`P1DT2H30M`, `PT45S`)
- an ISO 8601 date or datetime (`2024-01-01`, `2024-01-01T10:30:00`)
- `now`, or `none`/`null` where the function accepts `None`

| Subcommand | Arguments | Description |
| --- | --- | --- |
| `naturaldelta` | `value [--months/--no-months] [--minimum-unit U]` | Time delta without tense |
| `naturaltime` | `value [--future] [--months/--no-months] [--minimum-unit U] [--when DT]` | Time with tense |
| `naturalday` | `value [--format FMT]` | Today/yesterday/etc. |
| `naturaldate` | `value` | Like `naturalday`, with year |
| `precisedelta` | `value [--minimum-unit U] [--suppress U...] [--format FMT]` | Precise delta |

`--minimum-unit` for `naturaldelta` and `naturaltime` accepts only
`microseconds`, `milliseconds` or `seconds`; `precisedelta` accepts all units
shown in [Time](time.md).

### Locale formatters

| Subcommand | Arguments | Description |
| --- | --- | --- |
| `decimal_separator` | — | Decimal separator |
| `thousands_separator` | — | Thousands separator |

## Examples

```console
$ python -m humanize naturaltime 2024-01-01T00:00:00 --when 2024-01-02T00:00:00
a day ago
$ python -m humanize naturaldelta P1DT2H --no-months
a day
$ python -m humanize precisedelta 3633 --suppress seconds
1 hour and 0.55 minutes
$ python -m humanize intcomma 1234567 --json
{"command": "intcomma", "result": "1,234,567"}
$ python -m humanize naturaltime 3600 --locale de_DE
vor einer Stunde
```
