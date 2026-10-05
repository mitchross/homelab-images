#!/usr/bin/env bash
set -euo pipefail
for command in paseo claude codex pi agy mise node npm pnpm bun python python3 uv dotnet rustc cargo go java javac mvn gradle kubectl helm kustomize argocd talosctl omnictl gh op mink chezmoi crane yq docker temporal cilium jq rg git ssh chromium; do
  command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 1; }
done
node --version
bun --version
python --version
dotnet --list-sdks
rustc --version
cargo --version
go version
java -version
claude --version
codex --version
pi --version
agy --version
kubectl version --client=true
omnictl --help >/dev/null
mink --version
chezmoi --version
crane version
