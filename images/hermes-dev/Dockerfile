# syntax=docker/dockerfile:1
# Official Hermes Agent plus the coding agents and cluster CLIs its skills call.
FROM docker.io/nousresearch/hermes-agent:v0.22.5@sha256:9c5561579f3ffdf333401797094ac3a743738d6c25d40f4331c7bf77b694238d
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_VERSION=2.1.304
# renovate: datasource=npm depName=@openai/codex
ARG CODEX_VERSION=0.163.0
ARG GH_VERSION=2.102.0
ARG GH_SHA256=7e54a307f90afdc59796c325ec0c49fb09e6c18537727207a8ac7513584ea5b0
ARG KUBECTL_VERSION=1.37.1
ARG KUBECTL_SHA256=65691ff77eb6fa44c908b77a1082c9f092c3b9733b5cefabec0d1104890e21a8
# /opt/agents/bin goes first so the pinned CLIs win over anything on the data volume.
ENV PATH=/opt/agents/bin:${PATH} \
    DISABLE_AUTOUPDATER=1
RUN apt-get update && apt-get install -y --no-install-recommends tmux jq less openssh-client \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.deb" -o /tmp/gh.deb \
    && echo "$GH_SHA256  /tmp/gh.deb" | sha256sum -c - \
    && dpkg -i /tmp/gh.deb && rm /tmp/gh.deb
RUN curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl" -o /tmp/kubectl \
    && echo "$KUBECTL_SHA256  /tmp/kubectl" | sha256sum -c - \
    && install -m 0755 /tmp/kubectl /usr/local/bin/kubectl && rm /tmp/kubectl
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
      org.opencontainers.image.description="Hermes Agent with Claude Code, Codex, kubectl, gh and tmux"
# Stay root: s6-overlay bootstraps as root and drops the gateway to uid 10000 itself.
