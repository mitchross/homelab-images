#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
# Run as the runtime user with a read-only root and an empty /tmp, like the benchmark pod.
docker run --rm --user 65532:65532 --read-only --tmpfs /tmp:uid=65532,gid=65532 \
  --entrypoint /usr/local/bin/fio-image-smoke "$image"
docker run --rm --user 65532:65532 "$image" | grep -E '^fio-3\.[0-9]+'
