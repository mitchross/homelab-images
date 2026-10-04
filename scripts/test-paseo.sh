#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
python3 "$(dirname "$0")/test-pi.py" "$image"
name="paseo-smoke-${RANDOM}-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# An empty home catches tools accidentally installed under the image's /home.
docker run --rm --tmpfs /home/paseo:uid=1000,gid=1000 "$image" paseo-image-smoke
if docker run --rm "$image" > /dev/null 2>&1; then
  echo 'Daemon unexpectedly started without a password' >&2
  exit 1
fi
password=$(openssl rand -hex 32)
docker run -d --name "$name" --tmpfs /home/paseo:uid=1000,gid=1000 \
  -e "PASEO_PASSWORD=$password" -p 127.0.0.1::6767 "$image" >/dev/null
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
echo 'Fresh-home tools, password requirement, bundled UI, health and HTTP authentication passed.'
