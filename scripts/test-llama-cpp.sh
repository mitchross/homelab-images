#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
build=${2:?llama.cpp build number required}
# Runtime user, read-only root, empty home. CI has no GPU, so only the CPU backend loads.
run() {
  docker run --rm --user 65532:65532 --read-only --tmpfs /home/llama:uid=65532,gid=65532 "$@"
}
version="$(run "$image" --version 2>&1)" || { echo "$version"; exit 1; }
echo "$version"
grep -q "version: $build " <<< "$version"
run "$image" --list-devices 2>&1
run --entrypoint /app/llama-bench "$image" --help > /dev/null
run --entrypoint /app/llama-cli "$image" --version 2>&1 | tail -n 2
# Every library the CUDA backend needs must ship in the image, except the driver's libcuda.
missing="$(run --entrypoint ldd "$image" /app/libggml-cuda.so | awk '/not found/ { print $1 }')"
[[ "$missing" == "libcuda.so.1" ]] || { echo "unexpected missing libraries: $missing"; exit 1; }
echo ok
