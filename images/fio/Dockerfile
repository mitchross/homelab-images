# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183
# Storage benchmark pod: fio plus jq for parsing its JSON output.
# bash, coreutils, findutils and util-linux ship in the Debian base image.
FROM debian:trixie-slim@sha256:8aa5a7bf5a1955bddbe7d74fcdd0b91ab30e74362a8b73af672b0481b35b44a0
ARG FIO_VERSION=3.39-1
ARG JQ_VERSION=1.7.1-6+deb13u4
RUN apt-get update \
    && apt-get install -y --no-install-recommends "fio=$FIO_VERSION" "jq=$JQ_VERSION" \
    && rm -rf /var/lib/apt/lists/*
COPY scripts/smoke.sh /usr/local/bin/fio-image-smoke
ENV HOME=/tmp
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="fio storage benchmark with jq, for in-cluster volume tests"
USER 65532:65532
WORKDIR /tmp
CMD ["fio", "--version"]
