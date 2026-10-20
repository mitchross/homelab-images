#!/usr/bin/env bash
set -euo pipefail
for command in hermes claude codex git gh kubectl tmux jq rg node npm python3 ssh; do
  command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
mkdir -p "$HOME"
node --version
claude --version
codex --version
git --version
gh --version | head -1
kubectl version --client=true
tmux -V
