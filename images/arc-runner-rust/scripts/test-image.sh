#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
# The runner user, no network, like a job that must not download tools.
docker run --rm --network none --entrypoint /usr/local/bin/arc-runner-rust-smoke "$image"
# ARC's init container copies the runner externals out of this image.
docker run --rm --network none --entrypoint ls "$image" /home/runner/externals | grep -q node
docker run --rm --network none --entrypoint /home/runner/bin/Runner.Listener "$image" --version
