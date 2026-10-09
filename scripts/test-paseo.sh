#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
python3 "$(dirname "$0")/test-pi.py" "$image"
name="paseo-smoke-${RANDOM}-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# An empty home catches tools accidentally installed under the image's /home.
docker run --rm --tmpfs /home/paseo:uid=1000,gid=1000 "$image" paseo-image-smoke
# Exercise Cargo's writable registry and a native build as uid 1000.
docker run --rm --tmpfs /home/paseo:uid=1000,gid=1000 "$image" bash -ec '
  cd "$HOME"
  cargo new --bin cargo-smoke
  cd cargo-smoke
  echo "itoa = \"=1.0.15\"" >> Cargo.toml
  cargo build
'
# Paseo terminals are interactive non-login bash; the Pi launchers must load there.
docker run --rm --tmpfs /home/paseo:uid=1000,gid=1000 "$image" bash -ic 'type pi-qwen-only pi-withflash pi-flash' >/dev/null
if docker run --rm "$image" > /dev/null 2>&1; then
  echo 'Daemon unexpectedly started without a password' >&2
  exit 1
fi
password=$(openssl rand -hex 32)
managed=$(mktemp)
trap 'cleanup; rm -f "$managed"' EXIT
cat > "$managed" <<'JSON'
{"daemon": {"mcp": {"injectIntoAgents": true}, "browserTools": {"enabled": true},
  "agentProfiles": [{"id": "review", "name": "Review", "provider": "claude", "model": "claude-opus-5-5"}]}}
JSON
chmod 0644 "$managed"
docker run -d --name "$name" --tmpfs /home/paseo:uid=1000,gid=1000 \
  -e "PASEO_PASSWORD=$password" -e GITEA_URL=https://gitea.example.test -e GITEA_TOKEN=test-token \
  -e GITEA_LOGIN_NAME=example -e PASEO_MANAGED_CONFIG=/etc/paseo-managed.json \
  -v "$managed:/etc/paseo-managed.json:ro" -p 127.0.0.1::6767 "$image" >/dev/null
port=$(docker inspect --format '{{(index (index .NetworkSettings.Ports "6767/tcp") 0).HostPort}}' "$name")
origin="http://127.0.0.1:$port"
ready=false
for _ in $(seq 1 90); do
  if curl -fsS "$origin/api/health" >/dev/null 2>&1; then ready=true; break; fi
  sleep 1
done
if [[ $ready != true ]]; then docker logs "$name"; exit 1; fi
[[ $(curl -s -o /dev/null -w '%{http_code}' "$origin/") == 200 ]]
[[ $(curl -s -o /dev/null -w '%{http_code}' "$origin/api/status") == 401 ]]
[[ $(curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer wrong' "$origin/api/status") == 401 ]]
[[ $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $password" "$origin/api/status") == 200 ]]
# The daemon must keep the bundled Node ABI; agents retain mise's Node.
docker exec "$name" bash -ec '
  expected=$(readlink -f /usr/local/bin/node)
  found=false
  for process in /proc/[0-9]*/exe; do
    if [[ $(readlink "$process" || true) == "$expected" ]]; then found=true; fi
  done
  [[ $found == true ]]
'
# Runtime Gitea login and Git-managed Paseo settings must survive the daemon's own config load.
docker exec "$name" bash -ec '
  [[ $(yq ".logins[] | select(.name == \"example\") | .url" ~/.config/tea/config.yml) == https://gitea.example.test ]]
  [[ $(git config --global --get-all credential.https://gitea.example.test.helper) == "!tea login helper" ]]
  jq -e ".daemon.mcp.injectIntoAgents and .daemon.browserTools.enabled and .daemon.agentProfiles[0].id == \"review\"" ~/.paseo/config.json >/dev/null
'
echo 'Fresh-home tools, password requirement, bundled UI, health, HTTP authentication, Gitea login and managed config passed.'
