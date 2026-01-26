#!/usr/bin/env bash
set -euo pipefail

init_file="src/mokit_tui/__init__.py"
pyproject_file="pyproject.toml"

if [ "${1:-}" = "" ]; then
  version=$(sed -n 's/^__version__ *=[[:space:]]*"\([^"]\+\)"/\1/p' "$init_file")
  if [ -z "$version" ]; then
    echo "No version found in $init_file" >&2
    exit 1
  fi
  printf "%s\n" "$version"
  exit 0
fi

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "Usage: $0 <new_version>"
  echo "Example: $0 0.2.1"
  echo "No arguments prints current version."
  exit 0
fi

new_version="$1"

if ! grep -q '^__version__' "$init_file"; then
  echo "No version pattern found in $init_file" >&2
  exit 1
fi

if ! grep -q '^version[[:space:]]*=' "$pyproject_file"; then
  echo "No version pattern found in $pyproject_file" >&2
  exit 1
fi

sed -i "s/^__version__ *=[[:space:]]*\"[^\"]\+\"/__version__ = \"$new_version\"/" "$init_file"
sed -i "s/^version[[:space:]]*= *\"[^\"]\+\"/version = \"$new_version\"/" "$pyproject_file"

echo "Updated version to $new_version"
