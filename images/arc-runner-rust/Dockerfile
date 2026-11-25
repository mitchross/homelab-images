# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183
# ARC runner for Rust repos: the build tools, Rust toolchain and sccache that CI used to install per job.
FROM ghcr.io/actions/actions-runner:2.338.2@sha256:6d0b2d80d80f143f77dcb676e50920100bbb547e39e883454d57f45ab8c31300
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# renovate: datasource=github-tags depName=rust-lang/rustup
ARG RUSTUP_VERSION=1.29.3
# Keep in step with rust-toolchain.toml in the Rust repos; a different channel still works, rustup downloads it per job.
# renovate: datasource=github-releases depName=rust-lang/rust
ARG RUST_VERSION=1.100.0
# Bump SCCACHE_SHA256 by hand from the release's .tar.gz.sha256 asset; the build fails until it matches.
ARG SCCACHE_SHA256=c9f6c5a3ae84d9da0956b28c357a365827bda33f3383647fc0b67484c74a5ea9
# renovate: datasource=github-releases depName=mozilla/sccache extractVersion=^v(?<version>.+)$
ARG SCCACHE_VERSION=0.20.1
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake pkg-config protobuf-compiler libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://github.com/mozilla/sccache/releases/download/v${SCCACHE_VERSION}/sccache-v${SCCACHE_VERSION}-x86_64-unknown-linux-musl.tar.gz" -o /tmp/sccache.tgz \
    && echo "${SCCACHE_SHA256}  /tmp/sccache.tgz" | sha256sum -c - \
    && tar -xzf /tmp/sccache.tgz -C /tmp \
    && install -m 0755 "/tmp/sccache-v${SCCACHE_VERSION}-x86_64-unknown-linux-musl/sccache" /usr/local/bin/sccache \
    && rm -r /tmp/sccache.tgz "/tmp/sccache-v${SCCACHE_VERSION}-x86_64-unknown-linux-musl"
# Rust lives in the runner's home so rustup can still add a toolchain a repo pins differently.
USER runner
ENV PATH=/home/runner/.cargo/bin:${PATH}
RUN curl -fsSL "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" -o /tmp/rustup-init \
    && sha=$(curl -fsSL "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init.sha256" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && /tmp/rustup-init -y --no-modify-path --profile minimal \
         --default-toolchain "$RUST_VERSION" --component clippy,rustfmt \
    && rm /tmp/rustup-init \
    && rustup set auto-self-update disable
COPY --chmod=0755 scripts/smoke.sh /usr/local/bin/arc-runner-rust-smoke
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="GitHub Actions ARC runner with Rust, clippy, rustfmt, sccache, protoc and cmake"
