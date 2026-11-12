#!/usr/bin/env bash
set -euo pipefail
for command in fio jq bash find stat flock; do
  command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
test "$(id -u)" = 65532
fio --version
file=$(mktemp "${TMPDIR:-/tmp}/fio-smoke.XXXXXX")
trap 'rm -f "$file"' EXIT
fio --name=smoke --filename="$file" --size=4m --rw=randwrite --bs=4k --direct=0 \
  --output-format=json | jq -e '.jobs[0].write.io_bytes > 0' >/dev/null
echo "fio smoke job OK"
