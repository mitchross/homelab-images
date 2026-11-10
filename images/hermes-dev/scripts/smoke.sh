#!/usr/bin/env bash
set -euo pipefail
for command in hermes claude codex git gh kubectl helm kustomize bun bunx omnictl talosctl hubble tmux cargo rustc go protoc jq rg node npm python3 ssh; do
  command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
mkdir -p "$HOME"
node --version
claude --version
codex --version
git --version
gh --version | head -1
kubectl version --client=true
helm version --short
kustomize version
bun --version
omnictl --version
talosctl version --client --short
hubble version
rustc --version
cargo clippy --version
go version
test -f /usr/include/google/protobuf/timestamp.proto
tmux -V
