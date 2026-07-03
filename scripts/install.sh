#!/usr/bin/env bash
set -euo pipefail

force=false
if [[ "${1:-}" == "--force" ]]; then
  force=true
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
destination="${HOME}/.copilot/skills/experiment-loop"

if [[ ! -f "$source_dir/SKILL.md" ]]; then
  echo "Skill file not found: $source_dir" >&2
  exit 1
fi

if [[ -e "$destination" ]]; then
  if [[ "$force" != true ]]; then
    echo "Destination already exists: $destination. Re-run with --force to overwrite." >&2
    exit 1
  fi
  rm -rf "$destination"
fi

mkdir -p "$(dirname "$destination")"
mkdir -p "$destination"
for item in SKILL.md references templates examples README.md INSTALL.md PACKAGE_MANIFEST.json; do
  if [[ -e "$source_dir/$item" ]]; then
    cp -R "$source_dir/$item" "$destination/$item"
  fi
done
echo "Installed experiment-loop skill to $destination"
