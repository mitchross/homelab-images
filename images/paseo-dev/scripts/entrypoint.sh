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
# Rebuild the Gitea login from the runtime Secret on every start, so a rotated token applies.
if [[ -n "${GITEA_URL:-}" && -n "${GITEA_TOKEN:-}" ]]; then
  tea_config="$HOME/.config/tea/config.yml"
  mkdir -p "${tea_config%/*}"
  [[ -s "$tea_config" ]] || echo '{}' > "$tea_config"
  GITEA_LOGIN_NAME="${GITEA_LOGIN_NAME:-gitea}" GITEA_USER="${GITEA_USER:-}" \
    GITEA_HOST="$(sed -E 's#^https?://([^/:]+).*#\1#' <<<"$GITEA_URL")" \
    yq -i '.logins = [(.logins // [])[] | select(.name != strenv(GITEA_LOGIN_NAME))]
      + [{"name": strenv(GITEA_LOGIN_NAME), "url": strenv(GITEA_URL), "token": strenv(GITEA_TOKEN),
          "default": true, "ssh_host": strenv(GITEA_HOST), "user": strenv(GITEA_USER)}]' "$tea_config"
  chmod 0600 "$tea_config"
  git config --global --replace-all "credential.$GITEA_URL.helper" '!tea login helper'
fi
# Git owns the keys in PASEO_MANAGED_CONFIG; each start merges them over the user's config.json.
if [[ -n "${PASEO_MANAGED_CONFIG:-}" ]]; then
  paseo_config="${PASEO_HOME:-$HOME/.paseo}/config.json"
  mkdir -p "${paseo_config%/*}"
  [[ -s "$paseo_config" ]] || echo '{}' > "$paseo_config"
  jq -s '.[0] * .[1]' "$paseo_config" "$PASEO_MANAGED_CONFIG" > "$paseo_config.tmp"
  mv "$paseo_config.tmp" "$paseo_config"
fi
# Preserve the upstream Node ABI without changing PATH for spawned agents.
if [[ $# == 0 ]]; then
  exec /usr/local/bin/paseo-docker-entrypoint /usr/local/bin/node "$(cat /etc/paseo-server-entry)"
fi
exec /usr/local/bin/paseo-docker-entrypoint "$@"
