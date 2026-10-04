#!/usr/bin/env bash
set -euo pipefail
manifest=/opt/paseo-image/agy-release.json
curl -fsSL "$(jq -r .url "$manifest")" -o /tmp/agy.tar.gz
printf '%s  /tmp/agy.tar.gz\n' "$(jq -r .sha512 "$manifest")" | sha512sum -c -
mkdir /tmp/agy-unpack
tar -xzf /tmp/agy.tar.gz -C /tmp/agy-unpack
install -m 0755 /tmp/agy-unpack/antigravity /usr/local/bin/agy
rm -rf /tmp/agy.tar.gz /tmp/agy-unpack
