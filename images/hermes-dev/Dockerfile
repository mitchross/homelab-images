# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
# Official Hermes Agent plus the coding agents and cluster CLIs its skills call.
FROM docker.io/nousresearch/hermes-agent:v0.22.5@sha256:9c5561579f3ffdf333401797094ac3a743738d6c25d40f4331c7bf77b694238d
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_VERSION=2.1.312
# renovate: datasource=npm depName=@openai/codex
ARG CODEX_VERSION=0.165.0
# renovate: datasource=github-releases depName=cli/cli extractVersion=^v(?<version>.+)$
ARG GH_VERSION=2.103.3
# renovate: datasource=github-releases depName=kubernetes/kubernetes extractVersion=^v(?<version>.+)$
ARG KUBECTL_VERSION=1.37.2
# Downloads are checked against each release's published checksums.
# omnictl must match the Omni server release; talosctl follows the cluster's Talos version.
# renovate: datasource=github-releases depName=siderolabs/omni extractVersion=^v(?<version>.+)$
ARG OMNICTL_VERSION=1.13.0
# renovate: datasource=github-releases depName=siderolabs/talos extractVersion=^v(?<version>.+)$
ARG TALOSCTL_VERSION=1.14.5
# renovate: datasource=golang-version depName=go
ARG GO_VERSION=1.27.3
# renovate: datasource=github-tags depName=rust-lang/rustup
ARG RUSTUP_VERSION=1.29.2
# renovate: datasource=github-releases depName=rust-lang/rust
ARG RUST_VERSION=1.99.1
# /opt/agents/bin goes first so the pinned CLIs win over anything on the data volume.
# Rust toolchains are read-only in the image; cargo's registry cache lives on the volume.
ENV PATH=/opt/agents/bin:/opt/rust/cargo/bin:/usr/local/go/bin:${PATH} \
    RUSTUP_HOME=/opt/rust/rustup \
    DISABLE_AUTOUPDATER=1
RUN apt-get update && apt-get install -y --no-install-recommends tmux jq less openssh-client \
      build-essential pkg-config libssl-dev protobuf-compiler libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.deb" -o /tmp/gh.deb \
    && sha=$(curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_checksums.txt" | grep " gh_${GH_VERSION}_linux_amd64.deb$" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/gh.deb" | sha256sum -c - \
    && dpkg -i /tmp/gh.deb && rm /tmp/gh.deb
RUN curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl" -o /tmp/kubectl \
    && sha=$(curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256") \
    && echo "${sha:?no checksum}  /tmp/kubectl" | sha256sum -c - \
    && install -m 0755 /tmp/kubectl /usr/local/bin/kubectl && rm /tmp/kubectl
RUN curl -fsSL "https://github.com/siderolabs/omni/releases/download/v${OMNICTL_VERSION}/omnictl-linux-amd64" -o /tmp/omnictl \
    && sha=$(curl -fsSL "https://github.com/siderolabs/omni/releases/download/v${OMNICTL_VERSION}/sha256sum.txt" | grep " omnictl-linux-amd64$" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/omnictl" | sha256sum -c - \
    && install -m 0755 /tmp/omnictl /usr/local/bin/omnictl && rm /tmp/omnictl \
    && curl -fsSL "https://github.com/siderolabs/talos/releases/download/v${TALOSCTL_VERSION}/talosctl-linux-amd64" -o /tmp/talosctl \
    && sha=$(curl -fsSL "https://github.com/siderolabs/talos/releases/download/v${TALOSCTL_VERSION}/sha256sum.txt" | grep " talosctl-linux-amd64$" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/talosctl" | sha256sum -c - \
    && install -m 0755 /tmp/talosctl /usr/local/bin/talosctl && rm /tmp/talosctl
RUN curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tgz \
    && sha=$(curl -fsSL "https://dl.google.com/go/go${GO_VERSION}.linux-amd64.tar.gz.sha256") \
    && echo "${sha:?no checksum}  /tmp/go.tgz" | sha256sum -c - \
    && tar -C /usr/local -xzf /tmp/go.tgz && rm /tmp/go.tgz
RUN curl -fsSL "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init" -o /tmp/rustup-init \
    && sha=$(curl -fsSL "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init.sha256" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && CARGO_HOME=/opt/rust/cargo /tmp/rustup-init -y --no-modify-path --profile minimal \
         --default-toolchain "$RUST_VERSION" --component clippy,rustfmt \
    && rm /tmp/rustup-init && chmod -R a+rX /opt/rust
# npm 12 blocks install scripts by default; Claude Code fetches its native binary in postinstall.
RUN npm install --global --prefix /opt/agents --allow-scripts=@anthropic-ai/claude-code \
      "@anthropic-ai/claude-code@$CLAUDE_VERSION" \
      "@openai/codex@$CODEX_VERSION" \
    && npm cache clean --force \
    && chmod -R a+rX /opt/agents
COPY scripts/smoke.sh /usr/local/bin/hermes-image-smoke
RUN chmod 0755 /usr/local/bin/hermes-image-smoke \
    && HOME=/tmp/smoke-home setpriv --reuid=10000 --regid=10000 --clear-groups /usr/local/bin/hermes-image-smoke \
    && rm -rf /tmp/smoke-home
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="Hermes Agent with Claude Code, Codex, Rust, Go, kubectl, omnictl, talosctl, gh and tmux"
# Stay root: s6-overlay bootstraps as root and drops the gateway to uid 10000 itself.
