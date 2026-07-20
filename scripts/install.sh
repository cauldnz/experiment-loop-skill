#!/usr/bin/env bash
set -euo pipefail

force=false
runtime=both
destination=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) force=true ;;
    --runtime) shift; runtime="${1:?--runtime requires copilot, claude, or both}" ;;
    --destination) shift; destination="${1:?--destination requires a path}" ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

initialize_destination() {
  local path="$1"
  if [[ -e "$path" ]]; then
    if [[ "$force" != true ]]; then
      echo "Destination already exists: $path. Re-run with --force to overwrite." >&2
      exit 1
    fi
    rm -rf "$path"
  fi
  mkdir -p "$path"
}

install_loop() {
  local path="$1"
  initialize_destination "$path"
  for item in SKILL.md CONTEXT.md references templates examples docs scripts README.md INSTALL.md PACKAGE_MANIFEST.json requirements.txt; do
    if [[ -e "$source_dir/$item" ]]; then
      cp -R "$source_dir/$item" "$path/$item"
    fi
  done
  echo "Installed experiment-loop skill to $path"
  echo "Install dependencies: python \"$path/scripts/install_dependencies.py\""
}

install_setup() {
  local path="$1"
  initialize_destination "$path"
  mkdir -p "$path/references" "$path/scripts" "$path/templates"
  cp "$source_dir/skills/experiment-setup/SKILL.md" "$path/SKILL.md"
  cp "$source_dir/references/experiment-brief-schema-v1.0.json" "$path/references/"
  cp "$source_dir/references/experiment-approval-schema-v1.0.json" "$path/references/"
  cp "$source_dir/scripts/validate_experiment_setup.py" "$path/scripts/"
  cp "$source_dir/scripts/prepare_scratch.py" "$path/scripts/"
  cp "$source_dir/templates/experiment-brief-template.json" "$path/templates/"
  cp "$source_dir/templates/experiment-approval-template.json" "$path/templates/"
  echo "Installed experiment-setup skill to $path"
}

install_root() {
  local root="$1"
  install_loop "$root/experiment-loop"
  install_setup "$root/experiment-setup"
}

if [[ -n "$destination" ]]; then
  install_loop "$destination"
  install_setup "$(dirname "$destination")/experiment-setup"
else
  case "$runtime" in
    copilot|Copilot) install_root "$HOME/.copilot/skills" ;;
    claude|Claude) install_root "$HOME/.claude/skills" ;;
    both|Both)
      install_root "$HOME/.copilot/skills"
      install_root "$HOME/.claude/skills"
      ;;
    *) echo "--runtime must be copilot, claude, or both" >&2; exit 2 ;;
  esac
fi
