#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOME_DIR="${HOME:?HOME must be set}"
MARKETPLACE_FILE="${HOME_DIR}/.agents/plugins/marketplace.json"
INSTALL_ROOT="${HOME_DIR}/.codex/plugins"
MARKETPLACE_NAME="local-personal"
MARKETPLACE_DISPLAY_NAME="Local Personal"
INSTALL_STATE_REL=".codex-plugin/install-state.json"
INSTALLER_ID="engineering-design/install_codex_plugin.sh"
MODE="install"
DRY_RUN="false"

usage() {
  cat <<'EOF'
Usage:
  scripts/install_codex_plugin.sh [--dry-run]
  scripts/install_codex_plugin.sh --remove [--dry-run]

Options:
  --dry-run           Show what would change without modifying files.
  --remove            Remove the installed personal plugin copy and marketplace entry.
  --install-root DIR  Override the personal plugin install root. Default: ~/.codex/plugins
  --marketplace FILE  Override the personal marketplace file. Default: ~/.agents/plugins/marketplace.json
  --marketplace-name NAME
                      Set the marketplace name when creating a new file. Default: local-personal
  --marketplace-display-name NAME
                      Set the marketplace title shown in Codex when missing. Default: Local Personal
  -h, --help          Show this help message.
EOF
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN="true"
      ;;
    --remove)
      MODE="remove"
      ;;
    --install-root)
      shift
      [[ $# -gt 0 ]] || fail "--install-root requires a value"
      INSTALL_ROOT="$1"
      ;;
    --marketplace)
      shift
      [[ $# -gt 0 ]] || fail "--marketplace requires a value"
      MARKETPLACE_FILE="$1"
      ;;
    --marketplace-name)
      shift
      [[ $# -gt 0 ]] || fail "--marketplace-name requires a value"
      MARKETPLACE_NAME="$1"
      ;;
    --marketplace-display-name)
      shift
      [[ $# -gt 0 ]] || fail "--marketplace-display-name requires a value"
      MARKETPLACE_DISPLAY_NAME="$1"
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

command -v python3 >/dev/null 2>&1 || fail "python3 is required"
[[ -f "${REPO_ROOT}/.codex-plugin/plugin.json" ]] || fail "missing ${REPO_ROOT}/.codex-plugin/plugin.json"

ORIGIN_URL="$(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || true)"

PLUGIN_NAME="$(python3 - "${REPO_ROOT}/.codex-plugin/plugin.json" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
name = manifest.get("name")
if not isinstance(name, str) or not name:
    raise SystemExit("plugin manifest must define a non-empty string name")
print(name)
PY
)"

TARGET_DIR="${INSTALL_ROOT}/${PLUGIN_NAME}"

MARKETPLACE_ROOT="$(python3 - "${MARKETPLACE_FILE}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
if path.name != "marketplace.json":
    raise SystemExit("marketplace file must be named marketplace.json")
if path.parent.name != "plugins" or path.parent.parent.name != ".agents":
    raise SystemExit(
        "marketplace file must live under <root>/.agents/plugins/marketplace.json"
    )
print(path.parents[2])
PY
)"

PLUGIN_PATH="$(python3 - "${MARKETPLACE_ROOT}" "${TARGET_DIR}" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1]).expanduser().resolve()
target = Path(sys.argv[2]).expanduser().resolve()
try:
    rel = target.relative_to(root)
except ValueError as exc:
    raise SystemExit(
        f"plugin install path {target} must live under marketplace root {root}"
    ) from exc

rel_text = rel.as_posix()
if rel_text == ".":
    print("./")
else:
    print(f"./{rel_text}")
PY
)"

sync_plugin_tree() {
  run python3 - "${REPO_ROOT}" "${TARGET_DIR}" "${PLUGIN_NAME}" "${INSTALL_STATE_REL}" "${INSTALLER_ID}" "${ORIGIN_URL}" <<'PY'
import json
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).expanduser().resolve()
plugin_name = sys.argv[3]
state_rel = Path(sys.argv[4])
installer_id = sys.argv[5]
origin_url = sys.argv[6]
ignore = shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc", ".DS_Store")

manifest_path = source / ".codex-plugin" / "plugin.json"
skills_dir = source / "skills"
if not source.is_dir():
    raise SystemExit(f"source repo root not found: {source}")
if not manifest_path.is_file():
    raise SystemExit(f"missing plugin manifest: {manifest_path}")
if not skills_dir.is_dir():
    raise SystemExit(f"missing skills directory: {skills_dir}")
if not any(path.is_file() for path in skills_dir.glob("*/SKILL.md")):
    raise SystemExit(f"no skills found under {skills_dir}")

target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    if not target.is_dir():
        raise SystemExit(f"install target exists and is not a directory: {target}")
    state_path = target / state_rel
    if not state_path.is_file():
        raise SystemExit(
            f"install target already exists but is not managed by this installer: {target}"
        )
    state = json.loads(state_path.read_text())
    if state.get("pluginName") != plugin_name or state.get("installer") != installer_id:
        raise SystemExit(
            f"install target already exists with incompatible install state: {target}"
        )
    shutil.rmtree(target)

shutil.copytree(source, target, ignore=ignore)
state_path = target / state_rel
state_path.parent.mkdir(parents=True, exist_ok=True)
state_path.write_text(
    json.dumps(
        {
            "installer": installer_id,
            "pluginName": plugin_name,
            "sourceRepoRoot": str(source),
            "sourceOriginUrl": origin_url or None,
        },
        indent=2,
        ensure_ascii=False,
    )
    + "\n"
)
PY
}

validate_marketplace_install() {
  run python3 - "${MARKETPLACE_FILE}" "${PLUGIN_NAME}" "${PLUGIN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
plugin_name = sys.argv[2]
plugin_path = sys.argv[3]

if not path.exists():
    raise SystemExit(0)
if not path.is_file():
    raise SystemExit(f"{path} exists and is not a file")

data = json.loads(path.read_text())
if not isinstance(data, dict):
    raise SystemExit(f"{path} must contain a JSON object")

plugins = data.get("plugins")
if plugins is None:
    plugins = []
if not isinstance(plugins, list):
    raise SystemExit(f"{path} field 'plugins' must be an array")

matches = []
for entry in plugins:
    if not isinstance(entry, dict):
        raise SystemExit(f"{path} contains a non-object plugin entry")
    if entry.get("name") == plugin_name:
        matches.append(entry)

if len(matches) > 1:
    raise SystemExit(f"{path} contains multiple entries for plugin {plugin_name}")

if not matches:
    raise SystemExit(0)

source = matches[0].get("source")
existing_path = None
if isinstance(source, dict) and source.get("source") == "local":
    value = source.get("path")
    if isinstance(value, str):
        existing_path = value

if existing_path != plugin_path:
    raise SystemExit(
        f"{path} already contains {plugin_name} with source.path={existing_path}; refusing to overwrite"
    )
PY
}

update_marketplace() {
  run python3 - "${MODE}" "${MARKETPLACE_FILE}" "${PLUGIN_NAME}" "${PLUGIN_PATH}" "${MARKETPLACE_NAME}" "${MARKETPLACE_DISPLAY_NAME}" <<'PY'
import json
import tempfile
import sys
from pathlib import Path

mode, marketplace_file, plugin_name, plugin_path, marketplace_name, marketplace_display_name = sys.argv[1:7]
path = Path(marketplace_file).expanduser()

def local_source_path(entry):
    source = entry.get("source")
    if not isinstance(source, dict):
        return None
    if source.get("source") != "local":
        return None
    value = source.get("path")
    return value if isinstance(value, str) else None

def write_json_atomic(target_path, payload):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        temp_name = handle.name
    Path(temp_name).replace(target_path)

if mode == "remove" and not path.exists():
    print(f"Marketplace file not found: {path}")
    raise SystemExit(0)

if path.exists():
    if not path.is_file():
        raise SystemExit(f"{path} exists and is not a file")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
else:
    data = {
        "name": marketplace_name,
        "interface": {"displayName": marketplace_display_name},
        "plugins": [],
    }

plugins = data.get("plugins")
if plugins is None:
    plugins = []
if not isinstance(plugins, list):
    raise SystemExit(f"{path} field 'plugins' must be an array")

interface = data.get("interface")
if interface is None:
    interface = {}
if not isinstance(interface, dict):
    raise SystemExit(f"{path} field 'interface' must be an object when present")
if not interface.get("displayName"):
    interface["displayName"] = marketplace_display_name
data["interface"] = interface

matches = []
new_plugins = []
for entry in plugins:
    if not isinstance(entry, dict):
        raise SystemExit(f"{path} contains a non-object plugin entry")
    if entry.get("name") == plugin_name:
        matches.append(entry)
        continue
    new_plugins.append(entry)

if len(matches) > 1:
    raise SystemExit(f"{path} contains multiple entries for plugin {plugin_name}")

existing = matches[0] if matches else None

if mode == "install":
    if existing is not None:
        existing_path = local_source_path(existing)
        if existing_path != plugin_path:
            raise SystemExit(
                f"{path} already contains {plugin_name} with source.path={existing_path}; refusing to overwrite"
            )
    entry = dict(existing or {})
    entry["name"] = plugin_name
    entry["source"] = {"source": "local", "path": plugin_path}
    entry["policy"] = {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    entry["category"] = "Productivity"
    new_plugins.append(entry)
    data["plugins"] = new_plugins
    if not data.get("name"):
        data["name"] = marketplace_name
    write_json_atomic(path, data)
    print(f"Updated marketplace entry for {plugin_name}: {path}")
    raise SystemExit(0)

if existing is None:
    print(f"Marketplace entry not found for {plugin_name}: {path}")
    raise SystemExit(0)

existing_path = local_source_path(existing)
if existing_path != plugin_path:
    print(
        f"Left marketplace entry untouched for {plugin_name} because source.path differs: {existing_path}"
    )
    raise SystemExit(0)

data["plugins"] = new_plugins
write_json_atomic(path, data)
print(f"Removed marketplace entry for {plugin_name}: {path}")
PY
}

if [[ "${MODE}" == "install" ]]; then
  validate_marketplace_install
  sync_plugin_tree
  update_marketplace
  printf 'Installed %s to %s\n' "${PLUGIN_NAME}" "${TARGET_DIR}"
  printf 'Updated %s with source.path=%s\n' "${MARKETPLACE_FILE}" "${PLUGIN_PATH}"
  printf 'Restart Codex and open /plugins to install or refresh the plugin.\n'
  exit 0
fi

run python3 - "${TARGET_DIR}" "${PLUGIN_NAME}" "${INSTALL_STATE_REL}" "${INSTALLER_ID}" <<'PY'
import json
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1]).expanduser().resolve()
plugin_name = sys.argv[2]
state_rel = Path(sys.argv[3])
installer_id = sys.argv[4]

if not target.exists():
    print(f"Not found {target}")
    raise SystemExit(0)
if not target.is_dir():
    raise SystemExit(f"install target exists and is not a directory: {target}")

state_path = target / state_rel
if not state_path.is_file():
    raise SystemExit(
        f"refusing to remove unmanaged install target without install state: {target}"
    )

state = json.loads(state_path.read_text())
if state.get("pluginName") != plugin_name or state.get("installer") != installer_id:
    raise SystemExit(
        f"refusing to remove install target with incompatible install state: {target}"
    )

shutil.rmtree(target)
print(f"Removed {target}")
PY

update_marketplace
