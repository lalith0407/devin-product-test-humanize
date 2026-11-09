# Command line interface

Humanize ships a command line interface that exposes every public formatter as
a subcommand. It can be run as a module or via the `humanize` console script
installed with the package:

```console
$ python -m humanize intcomma 1234567
1,234,567
$ humanize naturalsize 3000000 --binary
2.9 MiB
```

Run `humanize --help` (or `python -m humanize --help`) to list all available
subcommands, and `humanize <command> --help` for the options of a single
formatter.

## Subcommands

| Command            | Arguments                                   |
| ------------------ | ------------------------------------------- |
| `ordinal`          | `value [--gender GENDER]`                   |
| `intcomma`         | `value [--ndigits N]`                       |
| `intword`          | `value [--format FMT]`                      |
| `apnumber`         | `value`                                     |
| `fractional`       | `value`                                     |
| `scientific`       | `value [--precision N]`                     |
| `clamp`            | `value [--format FMT] [--floor F] [--ceil C] [--floor-token T] [--ceil-token T]` |
| `metric`           | `value [--unit U] [--precision N]`          |
| `naturalsize`      | `value [--binary] [--gnu] [--format FMT]`   |
| `format_rate`      | `size_str [--per PER]`                      |
| `natural_list`     | `items...`                                  |
| `naturaldelta`     | `seconds [--minimum-unit U] [--no-months]`  |
| `naturaltime`      | `value [--future] [--minimum-unit U] [--no-months] [--when DATETIME]` |
| `naturalday`       | `value [--format FMT]`                      |
| `naturaldate`      | `value`                                     |
| `precisedelta`     | `seconds [--minimum-unit U] [--suppress U]... [--format FMT]` |
| `decimal_separator`| (none)                                      |
| `thousands_separator` | (none)                                   |

Numeric arguments are parsed as integers or floats when possible. Date and
datetime arguments must be ISO 8601 (for example `2024-06-01` or
`2024-06-01T12:30:00`); `naturaltime` also accepts a plain number of seconds.
`naturaldelta` and `precisedelta` take a number of seconds.

## Locale and JSON output

Every subcommand accepts `--locale LOCALE` to translate the output for that
call only, and `--json` to print the result as a JSON object:

```console
$ humanize intcomma 1234 --locale de_DE
1.234
$ humanize intcomma 1234 --json
{"command": "intcomma", "result": "1,234"}
```

## API reference

::: humanize.cli
