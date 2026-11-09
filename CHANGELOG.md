# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Releases are drafted from pull request labels by
[Release Drafter](https://github.com/release-drafter/release-drafter).

## Unreleased

### Added

- Command-line interface: `humanize <formatter> <value>` (also available as
  `python -m humanize`) with one subcommand per public formatter, plus `--locale` to
  format in a given locale and `--json` for machine-readable output. See the
  [CLI documentation](https://humanize.readthedocs.io/en/latest/cli/).
