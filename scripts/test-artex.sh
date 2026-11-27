#!/usr/bin/env bash
# Smoke test with the talos Deployment's identity: root server, every capability dropped except the
# ones the agent privilege drop needs, no-new-privileges, explicit -exec-uid/-exec-gid, loopback proxy.
set -euo pipefail
image=${1:?image required}
version=${2:?upstream version required}
# Same major as the talos Deployment and upstream CI (postgres:16-alpine).
postgres_image=postgres:16.16@sha256:ce81150802644ddfac1db4da9e63be6f2a3818aa6ee98a7a28838aeea65dc37a
caps=(CHOWN DAC_OVERRIDE FOWNER FSETID KILL SETGID SETUID)
id=$$
net=artex-test-$id
pg=artex-test-pg-$id
app=artex-test-app-$id

cleanup() {
  echo '--- artex log ---'
  docker logs "$app" 2>&1 | tail -n 80 || true
  docker rm -f "$app" "$pg" > /dev/null 2>&1 || true
  docker network rm "$net" > /dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create "$net" > /dev/null
docker run -d --name "$pg" --network "$net" \
  -e POSTGRES_USER=artex -e POSTGRES_PASSWORD=artex-ci -e POSTGRES_DB=artex "$postgres_image" > /dev/null
for _ in $(seq 60); do
  docker exec "$pg" pg_isready -U artex -d artex > /dev/null 2>&1 && break
  sleep 1
done
docker exec "$pg" pg_isready -U artex -d artex

cap_args=(--cap-drop ALL)
for cap in "${caps[@]}"; do cap_args+=(--cap-add "$cap"); done
# The LLM base URL points at a closed loopback port: startup must not need a model.
docker run -d --name "$app" --network "$net" "${cap_args[@]}" --security-opt no-new-privileges \
  -e "ARTEX_PG_DSN=postgres://artex:artex-ci@$pg:5432/artex?sslmode=disable" \
  -e ARTEX_JWT_KEY_DIR=/app/keys -e ARTEX_NOISE_PROFILE=quiet -e ARTEX_UPDATE_CHECK=0 \
  -e ARTEX_LLM_PROVIDER=ollama -e ARTEX_LLM_BASE_URL=http://127.0.0.1:9/v1 -e ARTEX_LLM_MODEL=ci \
  "$image" -addr :8787 -proxy 127.0.0.1:8788 -exec-uid 10001 -exec-gid 10001 > /dev/null
ip="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$app")"

for _ in $(seq 90); do
  curl -fsS --max-time 2 "http://$ip:8787/api/ready" > /dev/null 2>&1 && break
  [[ "$(docker inspect -f '{{.State.Running}}' "$app")" == true ]] || { echo 'artex exited'; exit 1; }
  sleep 2
done
curl -fsS "http://$ip:8787/api/ready" | grep -q '"ready":true'
curl -fsS "http://$ip:8787/api/health" | grep -q '"ok":true'

logs="$(docker logs "$app" 2>&1)"
snapshot="$(grep -m1 '\[config\] snapshot ' <<< "$logs")"
echo "$snapshot"
grep -q "\"version\":\"$version\"" <<< "$snapshot"
grep -q '"proxy":"127.0.0.1:8788"' <<< "$snapshot"
grep -q '"noise_profile":"quiet"' <<< "$snapshot"
grep -q '"key_dir":"/app/keys"' <<< "$snapshot"
if grep -q 'same-uid isolation unavailable' <<< "$logs"; then echo 'privilege drop not applied'; exit 1; fi

# The recording proxy listens on loopback only: nothing answers on the pod address.
if curl -s --max-time 3 -o /dev/null "http://$ip:8788/"; then echo 'proxy reachable off loopback'; exit 1; fi

# Executor home and keys: the drop owns its home, root keeps the keys.
[[ "$(docker exec "$app" stat -c '%u:%g %a' /app/data/exec-home)" == '10001:10001 700' ]]
[[ "$(docker exec "$app" stat -c '%u %a' /app/keys/secret.key)" == '0 600' ]]

# An agent command drops to 10001 and cannot read the keys.
[[ "$(docker exec "$app" /app/artex __artex-exec-drop 10001 10001 -- id -u)" == 10001 ]]
if docker exec "$app" /app/artex __artex-exec-drop 10001 10001 -- cat /app/keys/secret.key > /dev/null 2>&1; then
  echo 'executor can read /app/keys/secret.key'; exit 1
fi

# Restart keeps the data: the supervisor relaunches and Postgres state survives.
docker restart "$app" > /dev/null
ip="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$app")"
for _ in $(seq 60); do
  curl -fsS --max-time 2 "http://$ip:8787/api/ready" 2> /dev/null | grep -q '"ready":true' && break
  sleep 2
done
curl -fsS "http://$ip:8787/api/ready" | grep -q '"ready":true'
echo ok
