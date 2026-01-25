# Versioning Protocol

## Scope

This project keeps version information in:

- `src/mokit_tui/__init__.py` (`__version__`)
- `pyproject.toml` (`[project].version`)

## Procedure

1) Update the version in `src/mokit_tui/__init__.py`.
2) Update the version in `pyproject.toml`.
3) Ensure both values match exactly.

## Pre-release Tags

Use PEP 440-compatible tags for pre-releases, for example:

- `0.2.0rc1`
