#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
# Tools must work as the hermes user with an empty data volume, like a fresh PVC.
docker run --rm --tmpfs /opt/data:uid=10000,gid=10000 --user 10000:10000 -e HOME=/opt/data \
  --entrypoint /usr/local/bin/hermes-image-smoke "$image"
# The container must still boot its s6 tree as root and report the Hermes version.
docker run --rm --tmpfs /opt/data:uid=10000,gid=10000 "$image" --version | grep -E 'Hermes Agent v0\.[0-9]+'
