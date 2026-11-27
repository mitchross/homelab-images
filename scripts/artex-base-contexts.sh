#!/usr/bin/env bash
# Print buildx --build-context lines that pin every external image in the Dockerfile to BASE_IMAGES.
# Fails if the Dockerfile names an image BASE_IMAGES lacks, or BASE_IMAGES has one the Dockerfile no longer uses.
set -euo pipefail
dockerfile=${1:?Dockerfile required}
pins=${2:?BASE_IMAGES required}

used="$(awk '
  toupper($1) == "FROM" {
    i = 2; while ($i ~ /^--/) i++
    if (!(tolower($i) in stage)) print $i
    if (toupper($(i + 1)) == "AS") stage[tolower($(i + 2))] = 1
  }
  toupper($1) ~ /^(COPY|RUN)$/ {
    for (i = 2; i <= NF; i++) if ($i ~ /^--from=/) {
      from = substr($i, 8); if (!(tolower(from) in stage) && from !~ /^[0-9]+$/) print from
    }
  }' "$dockerfile" | sort -u)"
pinned="$(grep -v '^[[:space:]]*$' "$pins" | sed 's/@.*//' | sort -u)"

while read -r line; do
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^[a-z0-9][a-z0-9./_-]*:[A-Za-z0-9._-]+@sha256:[0-9a-f]{64}$ ]] || { echo "bad pin: $line" >&2; exit 1; }
done < "$pins"
if [[ "$used" != "$pinned" ]]; then
  echo "Dockerfile base images and $pins differ:" >&2
  diff <(echo "$used") <(echo "$pinned") >&2 || true
  exit 1
fi
while read -r ref; do
  [[ -n "$ref" ]] && printf '%s=docker-image://%s\n' "${ref%@*}" "$ref"
done < "$pins"
