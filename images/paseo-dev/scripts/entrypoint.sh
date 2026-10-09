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
# Git owns each second-level key in PASEO_MANAGED_CONFIG: it replaces it whole, and null deletes it.
if [[ -n "${PASEO_MANAGED_CONFIG:-}" ]]; then
  paseo_config="${PASEO_HOME:-$HOME/.paseo}/config.json"
  mkdir -p "${paseo_config%/*}"
  [[ -s "$paseo_config" ]] || echo '{}' > "$paseo_config"
  merged=$(umask 077 && mktemp "$paseo_config.XXXXXX")
  jq -s '.[0] as $user | reduce (.[1] | to_entries[]) as $e ($user;
    .[$e.key] = if ($e.value | type) == "object"
      then (.[$e.key] // {}) + $e.value | with_entries(select(.value != null)) else $e.value end)' \
    "$paseo_config" "$PASEO_MANAGED_CONFIG" > "$merged"
  mv "$merged" "$paseo_config"
fi
# Preserve the upstream Node ABI without changing PATH for spawned agents.
if [[ $# == 0 ]]; then
  exec /usr/local/bin/paseo-docker-entrypoint /usr/local/bin/node "$(cat /etc/paseo-server-entry)"
fi
exec /usr/local/bin/paseo-docker-entrypoint "$@"
