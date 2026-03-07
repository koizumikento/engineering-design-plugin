#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"
TARGET_ROOT="${CODEX_HOME}/skills"

MODE="link"
DRY_RUN="false"
FORCE="false"

usage() {
  cat <<'EOF'
Usage:
  scripts/link_codex_skills.sh [--dry-run] [--force]
  scripts/link_codex_skills.sh --remove [--dry-run]

Options:
  --dry-run  Show what would change without modifying ~/.codex.
  --force    Replace conflicting paths under ~/.codex/skills.
  --remove   Remove links created for this repository.
  -h, --help Show this help message.

Environment:
  CODEX_HOME Override the Codex home directory (default: ~/.codex).
EOF
}

run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

status_label() {
  local action="$1"
  if [[ "${DRY_RUN}" == "true" ]]; then
    printf 'Would %s' "${action}"
  else
    printf '%s' "${action}"
  fi
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN="true"
      ;;
    --force)
      FORCE="true"
      ;;
    --remove)
      MODE="remove"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
  shift
done

if [[ ! -d "${REPO_ROOT}/skills" ]]; then
  fail "skills directory not found under ${REPO_ROOT}"
fi

run mkdir -p "${TARGET_ROOT}"

SKILL_DIRS=(
  "spec-writing"
  "mechanical-cad"
  "circuit-design"
  "integration"
)

for skill_dir in "${SKILL_DIRS[@]}"; do
  source_path="${REPO_ROOT}/skills/${skill_dir}"
  target_path="${TARGET_ROOT}/engineering-design-${skill_dir}"

  [[ -f "${source_path}/SKILL.md" ]] || fail "missing SKILL.md in ${source_path}"

  if [[ "${MODE}" == "remove" ]]; then
    if [[ -L "${target_path}" ]]; then
      resolved_target="$(readlink "${target_path}")"
      if [[ "${resolved_target}" == "${source_path}" ]]; then
        run rm "${target_path}"
        printf '%s %s\n' "$(status_label "remove")" "${target_path}"
      else
        printf 'Skipped %s (points to %s)\n' "${target_path}" "${resolved_target}"
      fi
    elif [[ -e "${target_path}" ]]; then
      printf 'Skipped %s (not a symlink)\n' "${target_path}"
    else
      printf 'Not found %s\n' "${target_path}"
    fi
    continue
  fi

  if [[ -L "${target_path}" ]]; then
    resolved_target="$(readlink "${target_path}")"
    if [[ "${resolved_target}" == "${source_path}" ]]; then
      printf 'Already linked %s -> %s\n' "${target_path}" "${source_path}"
      continue
    fi
    if [[ "${FORCE}" != "true" ]]; then
      fail "${target_path} already exists and points to ${resolved_target}; rerun with --force"
    fi
    run rm "${target_path}"
  elif [[ -e "${target_path}" ]]; then
    if [[ "${FORCE}" != "true" ]]; then
      fail "${target_path} already exists; rerun with --force"
    fi
    run rm -rf "${target_path}"
  fi

  run ln -s "${source_path}" "${target_path}"
  printf '%s %s -> %s\n' "$(status_label "link")" "${target_path}" "${source_path}"
done

if [[ "${MODE}" == "link" ]]; then
  printf '\nRestart Codex to pick up newly linked skills.\n'
fi
