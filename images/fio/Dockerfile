# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
# Storage benchmark pod: fio plus jq for parsing its JSON output.
# bash, coreutils, findutils and util-linux ship in the Debian base image.
FROM debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2
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
