# Command-line interface

Every public formatter is also available from the command line, either through the
`humanize` console script installed with the package or with `python -m humanize`:

```console
$ humanize intcomma 1234567
1,234,567
$ python -m humanize naturalsize 3000000
3.0 MB
```

## Usage

```text
humanize <formatter> <value> [options] [--locale L] [--json]
humanize --version
humanize --help
humanize <formatter> --help
```

The subcommand name is the name of the formatter function, the value is given as a
positional argument and the function's keyword arguments are available as options
(underscores become dashes, so `minimum_unit` is `--minimum-unit`). Negative numbers
such as `-1000`, `-1e3` and `-inf` are accepted as values.

The result is printed on standard output followed by a newline and the exit status is
`0`. If the value cannot be parsed or formatted, or the locale is not available, an
error message is printed on standard error and the exit status is `1`. Invalid usage,
such as an unknown subcommand or option, exits with status `2`.

## Common options

These options are accepted by every subcommand, after the value:

| Option       | Description                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------- |
| `--locale L` | Activate locale `L` (for example `de_DE`) for this call. By default no translation is used. |
| `--json`     | Print a JSON object instead of the plain result.                                            |
| `-h, --help` | Show the subcommand's help and exit.                                                        |

```console
$ humanize intcomma 1234567 --locale de_DE
1.234.567
$ humanize intword 1200000 --locale de_DE
1,2 Millionen
```

The locale is deactivated again after formatting. See [Internationalisation](i18n.md)
for the available locales.

With `--json`, a single JSON object is printed with the formatter name, the value as
given on the command line (a list for `natural_list`), the locale (or `null`) and the
result:

```console
$ humanize intcomma 1234567 --locale de_DE --json
{"formatter": "intcomma", "value": "1234567", "locale": "de_DE", "result": "1.234.567"}
$ humanize natural_list cats dogs mice --json
{"formatter": "natural_list", "value": ["cats", "dogs", "mice"], "locale": null, "result": "cats, dogs and mice"}
```

## Number formatters

Numeric values are parsed as integers where possible and as floats otherwise, except for
`clamp` and `metric` which always use floats.

### apnumber

Spell out numbers 1-9 in Associated Press style. See
[`apnumber`](number.md#humanize.number.apnumber).

```console
$ humanize apnumber 4
four
```

### clamp

Clamp a number between a floor and a ceiling. See
[`clamp`](number.md#humanize.number.clamp).

| Option                | Default | Description                                      |
| --------------------- | ------- | ------------------------------------------------ |
| `--format FORMAT`     | `{:}`   | `str.format` string for the value.               |
| `--floor FLOOR`       | none    | Lowest value before clamping (float).            |
| `--ceil CEIL`         | none    | Highest value before clamping (float).           |
| `--floor-token TOKEN` | `<`     | Prefix used when the value is below the floor.   |
| `--ceil-token TOKEN`  | `>`     | Prefix used when the value is above the ceiling. |

```console
$ humanize clamp 0.0001 --floor 0.01 --format '{:.0%}'
<1%
$ humanize clamp 0.999 --ceil 0.99 --format '{:.0%}'
>99%
```

### fractional

Convert a number to a fraction. See
[`fractional`](number.md#humanize.number.fractional).

```console
$ humanize fractional 1.3
1 3/10
```

### intcomma

Add thousands separators to a number. See
[`intcomma`](number.md#humanize.number.intcomma).

| Option        | Default | Description                         |
| ------------- | ------- | ----------------------------------- |
| `--ndigits N` | none    | Number of digits to round to (int). |

```console
$ humanize intcomma 1234567
1,234,567
$ humanize intcomma 1234567.891 --ndigits 2
1,234,567.89
```

### intword

Convert a large number to a friendly word form. See
[`intword`](number.md#humanize.number.intword).

| Option            | Default | Description                       |
| ----------------- | ------- | --------------------------------- |
| `--format FORMAT` | `%.1f`  | `%`-format string for the number. |

```console
$ humanize intword 1234567890 --format %.2f
1.23 billion
```

### metric

Format a number with a metric SI prefix. See
[`metric`](number.md#humanize.number.metric).

| Option          | Default | Description                          |
| --------------- | ------- | ------------------------------------ |
| `--unit UNIT`   | empty   | Unit suffix, for example `V` or `m`. |
| `--precision N` | `3`     | Number of significant digits (int).  |

```console
$ humanize metric 1500 --unit V
1.50 kV
$ humanize metric 0.00022 --unit F --precision 2
220 μF
```

### ordinal

Convert an integer to its ordinal. See [`ordinal`](number.md#humanize.number.ordinal).

| Option                   | Default | Description                       |
| ------------------------ | ------- | --------------------------------- |
| `--gender {male,female}` | `male`  | Gender used by some translations. |

```console
$ humanize ordinal 3
3rd
$ humanize ordinal 1 --locale fr_FR --gender female
1ère
```

### scientific

Format a number in scientific notation. See
[`scientific`](number.md#humanize.number.scientific).

| Option          | Default | Description                     |
| --------------- | ------- | ------------------------------- |
| `--precision N` | `2`     | Number of decimal places (int). |

```console
$ humanize scientific 299792458 --precision 3
2.998 x 10⁸
```

## File size

### naturalsize

Format a number of bytes as a file size. See
[`naturalsize`](filesize.md#humanize.filesize.naturalsize).

| Option            | Default | Description                                      |
| ----------------- | ------- | ------------------------------------------------ |
| `--binary`        | off     | Use binary prefixes (powers of 1024, `KiB`).     |
| `--gnu`           | off     | Use GNU-style single-letter suffixes (`K`, `M`). |
| `--format FORMAT` | `%.1f`  | `%`-format string for the number.                |

```console
$ humanize naturalsize 3000
3.0 kB
$ humanize naturalsize 3000 --binary
2.9 KiB
$ humanize naturalsize 3000 --gnu
2.9K
```

## Lists

### natural_list

Join one or more items into a human-readable list. Every remaining positional argument
is an item. See [`natural_list`](lists.md#humanize.lists.natural_list).

```console
$ humanize natural_list cats dogs mice
cats, dogs and mice
```

## Time formatters

Dates and datetimes are given in ISO 8601 format, for example `2007-06-05` or
`2007-06-05T12:00:00`. Durations are given as a number of seconds.

### naturaldate

Format a date naturally, including the year if it is far away. The value is an ISO 8601
date or datetime. See [`naturaldate`](time.md#humanize.time.naturaldate).

```console
$ humanize naturaldate 2007-06-05
Jun 05 2007
```

### naturalday

Format a date as `today`, `tomorrow` or `yesterday`, or else as a date string. The value
is an ISO 8601 date or datetime. See [`naturalday`](time.md#humanize.time.naturalday).

| Option            | Default | Description                                                          |
| ----------------- | ------- | -------------------------------------------------------------------- |
| `--format FORMAT` | `%b %d` | `strftime` format for dates other than today, tomorrow or yesterday. |

```console
$ humanize naturalday 2007-06-05 --format %Y-%m-%d
2007-06-05
```

### naturaldelta

Format a time delta naturally, without tense. The value is a number of seconds. See
[`naturaldelta`](time.md#humanize.time.naturaldelta).

| Option                    | Default    | Description                                               |
| ------------------------- | ---------- | --------------------------------------------------------- |
| `--months`, `--no-months` | `--months` | Whether to use months between days and years.             |
| `--minimum-unit UNIT`     | `seconds`  | Lowest unit: `seconds`, `milliseconds` or `microseconds`. |

```console
$ humanize naturaldelta 3600
an hour
$ humanize naturaldelta 0.002 --minimum-unit milliseconds
2 milliseconds
$ humanize naturaldelta 40000000 --no-months
1 year, 97 days
```

### naturaltime

Format a time relative to now, with tense. The value is either a number of seconds in
the past (or in the future with `--future`) or an ISO 8601 datetime. See
[`naturaltime`](time.md#humanize.time.naturaltime).

| Option                    | Default    | Description                                                      |
| ------------------------- | ---------- | ---------------------------------------------------------------- |
| `--future`                | off        | Treat a number of seconds as in the future rather than the past. |
| `--months`, `--no-months` | `--months` | Whether to use months between days and years.                    |
| `--minimum-unit UNIT`     | `seconds`  | Lowest unit: `seconds`, `milliseconds` or `microseconds`.        |
| `--when WHEN`             | now        | ISO 8601 datetime to compare against.                            |

```console
$ humanize naturaltime 3600
an hour ago
$ humanize naturaltime 3600 --future
an hour from now
$ humanize naturaltime 2007-06-05T12:00:00 --when 2007-06-05T13:00:00
an hour ago
```

### precisedelta

Format a time delta precisely. The value is a number of seconds. See
[`precisedelta`](time.md#humanize.time.precisedelta).

| Option                | Default   | Description                                                                                              |
| --------------------- | --------- | -------------------------------------------------------------------------------------------------------- |
| `--minimum-unit UNIT` | `seconds` | Lowest unit: `microseconds`, `milliseconds`, `seconds`, `minutes`, `hours`, `days`, `months` or `years`. |
| `--suppress UNIT`     | none      | Unit to leave out, from the same list. May be repeated.                                                  |
| `--format FORMAT`     | `%0.2f`   | `%`-format string for the fractional part of the smallest unit.                                          |

```console
$ humanize precisedelta 3725
1 hour, 2 minutes and 5 seconds
$ humanize precisedelta 3725.5 --suppress minutes
1 hour and 125.50 seconds
```
