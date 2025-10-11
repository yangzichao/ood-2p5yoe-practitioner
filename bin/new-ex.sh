#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR%/bin}"

python3 "${SCRIPT_DIR}/new-ex.py" "$@"
# Touch settings to make Gradle re-scan projects next run
touch "${REPO_ROOT}/settings.gradle.kts"
