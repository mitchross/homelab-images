# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
# Official Hermes Agent plus the coding agents and cluster CLIs its skills call.
FROM docker.io/nousresearch/hermes-agent:v0.23.0@sha256:adb7890916de63245523492be8f68f9d2095fecbec4e2a6dab7960381f0fc002
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_VERSION=2.1.321
# renovate: datasource=npm depName=@openai/codex
ARG CODEX_VERSION=0.167.0
# renovate: datasource=github-releases depName=cli/cli extractVersion=^v(?<version>.+)$
ARG GH_VERSION=2.103.3
# renovate: datasource=github-releases depName=kubernetes/kubernetes extractVersion=^v(?<version>.+)$
ARG KUBECTL_VERSION=1.37.2
# Downloads are checked against each release's published checksums.
# omnictl must match the Omni server release; talosctl follows the cluster's Talos version.
# renovate: datasource=github-releases depName=siderolabs/omni extractVersion=^v(?<version>.+)$
ARG OMNICTL_VERSION=1.13.2
# renovate: datasource=github-releases depName=siderolabs/talos extractVersion=^v(?<version>.+)$
ARG TALOSCTL_VERSION=1.14.5
# hubble reads flows from the cluster's hubble-relay; keep it near the Cilium release.
# renovate: datasource=github-releases depName=cilium/hubble extractVersion=^v(?<version>.+)$
ARG HUBBLE_VERSION=1.20.4
# helm and kustomize render charts and overlays for GitOps PRs; bun runs the JS repos' installs and tests.
# renovate: datasource=github-releases depName=helm/helm extractVersion=^v(?<version>.+)$
ARG HELM_VERSION=4.3.1
# renovate: datasource=github-releases depName=kubernetes-sigs/kustomize extractVersion=^kustomize/v(?<version>.+)$
ARG KUSTOMIZE_VERSION=5.8.3
# renovate: datasource=github-releases depName=oven-sh/bun extractVersion=^bun-v(?<version>.+)$
ARG BUN_VERSION=1.4.4
# renovate: datasource=golang-version depName=go
ARG GO_VERSION=1.27.3
# renovate: datasource=pypi depName=pytest
ARG PYTEST_VERSION=9.2.0
# renovate: datasource=github-tags depName=rust-lang/rustup
ARG RUSTUP_VERSION=1.29.3
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
    && install -m 0755 /tmp/talosctl /usr/local/bin/talosctl && rm /tmp/talosctl \
    && curl -fsSL "https://github.com/cilium/hubble/releases/download/v${HUBBLE_VERSION}/hubble-linux-amd64.tar.gz" -o /tmp/hubble.tgz \
    && sha=$(curl -fsSL "https://github.com/cilium/hubble/releases/download/v${HUBBLE_VERSION}/hubble-linux-amd64.tar.gz.sha256sum" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/hubble.tgz" | sha256sum -c - \
    && tar -C /usr/local/bin -xzf /tmp/hubble.tgz hubble && rm /tmp/hubble.tgz
RUN curl -fsSL "https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz" -o /tmp/helm.tgz \
    && sha=$(curl -fsSL "https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz.sha256sum" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/helm.tgz" | sha256sum -c - \
    && tar -C /usr/local/bin -xzf /tmp/helm.tgz --strip-components=1 linux-amd64/helm && rm /tmp/helm.tgz \
    && curl -fsSL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz" -o /tmp/kustomize.tgz \
    && sha=$(curl -fsSL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/checksums.txt" | grep " kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz$" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/kustomize.tgz" | sha256sum -c - \
    && tar -C /usr/local/bin -xzf /tmp/kustomize.tgz kustomize && rm /tmp/kustomize.tgz \
    && curl -fsSL "https://github.com/oven-sh/bun/releases/download/bun-v${BUN_VERSION}/bun-linux-x64.zip" -o /tmp/bun.zip \
    && sha=$(curl -fsSL "https://github.com/oven-sh/bun/releases/download/bun-v${BUN_VERSION}/SHASUMS256.txt" | grep " bun-linux-x64.zip$" | cut -d' ' -f1) \
    && echo "${sha:?no checksum}  /tmp/bun.zip" | sha256sum -c - \
    && python3 -m zipfile -e /tmp/bun.zip /tmp && install -m 0755 /tmp/bun-linux-x64/bun /usr/local/bin/bun \
    && ln -s bun /usr/local/bin/bunx && rm -rf /tmp/bun.zip /tmp/bun-linux-x64
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
# python3 on PATH is the Hermes venv (no pip); pytest adds only iniconfig and pluggy to it.
RUN /usr/local/bin/python3 -m pip --python /opt/hermes/.venv/bin/python install --no-cache-dir "pytest==${PYTEST_VERSION}"
COPY scripts/smoke.sh /usr/local/bin/hermes-image-smoke
RUN chmod 0755 /usr/local/bin/hermes-image-smoke \
    && HOME=/tmp/smoke-home setpriv --reuid=10000 --regid=10000 --clear-groups /usr/local/bin/hermes-image-smoke \
    && rm -rf /tmp/smoke-home
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="Hermes Agent with Claude Code, Codex, Rust, Go, bun, kubectl, helm, kustomize, omnictl, talosctl, hubble, gh and tmux"
# Stay root: s6-overlay bootstraps as root and drops the gateway to uid 10000 itself.
