#!/usr/bin/env bash
# Runs as the runner user with no network: everything CI needs must already be in the image.
set -euo pipefail
for command in cargo rustc rustup sccache cc c++ make cmake pkg-config protoc git docker curl jq; do
  command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
test "$(id -un)" = runner
test -x /home/runner/run.sh && test -d /home/runner/externals
test -f /usr/include/google/protobuf/timestamp.proto
rustc --version
cargo clippy --version
cargo fmt --version
sccache --version
protoc --version
cmake --version | head -1
test -w "$(rustup show home)"
work=$(mktemp -d)
trap 'sccache --stop-server >/dev/null 2>&1 || true; rm -r "$work"' EXIT
cd "$work"
# A repo pinning the baked toolchain must not trigger a download.
printf '[toolchain]\nchannel = "%s"\ncomponents = ["clippy", "rustfmt"]\nprofile = "minimal"\n' \
  "$(rustc --version | cut -d' ' -f2)" > rust-toolchain.toml
cargo new --quiet --vcs none smoke
mv rust-toolchain.toml smoke/
cd smoke
rustup toolchain install
cargo fmt --check
cargo clippy --quiet -- -D warnings
export SCCACHE_DIR=$work/sccache RUSTC_WRAPPER=sccache
sccache --start-server
cargo build --quiet --release
./target/release/smoke | grep -q 'Hello, world!'
sccache --show-stats --stats-format json | jq -e '.stats.requests_executed > 0' >/dev/null
echo "arc-runner-rust smoke OK"
