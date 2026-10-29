#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${REF2GAME_PYTHON:-python3}" "$HERE/setup.py" "$@"
