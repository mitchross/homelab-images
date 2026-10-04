#!/usr/bin/env bash
set -euo pipefail
if [[ $# == 0 && -z "${PASEO_PASSWORD:-}" ]]; then
  echo 'PASEO_PASSWORD must be supplied from a runtime Secret.' >&2
  exit 1
fi
# Copy defaults only on first use; upgrades must preserve user-owned settings.
mkdir -p "$HOME/.pi/agent" "$HOME/.codex" "$HOME/.claude"
if [[ ! -e "$HOME/.pi/agent/settings.json" ]]; then
  cp /etc/paseo-defaults/pi-settings.json "$HOME/.pi/agent/settings.json"
fi
if [[ ! -e "$HOME/.pi/agent/models.json" ]]; then
  cp /etc/paseo-defaults/pi-models.json "$HOME/.pi/agent/models.json"
fi
exec /usr/local/bin/paseo-docker-entrypoint "$@"
