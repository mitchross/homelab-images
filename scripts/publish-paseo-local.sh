#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
if [[ -n $(git status --porcelain) ]]; then
  echo 'Commit changes before publishing a traceable image.' >&2
  exit 1
fi
revision=$(git rev-parse HEAD)
image="ghcr.io/mitchross/paseo-dev:local-${revision}-$(date -u +%Y%m%d%H%M%S)"
# The persistent local Docker builder retains layers across invocations.
docker build --platform linux/amd64 --label "org.opencontainers.image.revision=$revision" \
  -t "$image" images/paseo-dev
bash scripts/test-paseo.sh "$image"
# Keep login credentials out of the normal Docker config and build context.
config=$(mktemp -d)
trap 'rm -rf "$config"' EXIT
gh auth token | docker --config "$config" login ghcr.io --username "$(gh api user --jq .login)" --password-stdin
docker --config "$config" push "$image"
docker inspect --format '{{index .RepoDigests 0}}' "$image"
