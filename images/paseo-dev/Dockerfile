# syntax=docker/dockerfile:1
FROM ghcr.io/getpaseo/paseo:0.10.3@sha256:100ae017b9fc45f167668be27e6abd82c5f7b14d512eb7f52a33f653a13bc34e AS tools
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG TARGETARCH
ARG MISE_VERSION=2026.9.14
ARG MISE_SHA256=343b133839d6a1d6c92daca90c4dbf7981dc28de8d308e5198a4ef24df8f5338
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_VERSION=2.1.289
# renovate: datasource=npm depName=@openai/codex
ARG CODEX_VERSION=0.160.0
# renovate: datasource=npm depName=@earendil-works/pi-coding-agent
ARG PI_VERSION=1.0.2
ENV MISE_DATA_DIR=/opt/mise \
    MISE_CACHE_DIR=/tmp/mise-cache \
    MISE_GLOBAL_CONFIG_FILE=/etc/mise/config.toml \
    MISE_YES=1 \
    MISE_RUSTUP_HOME=/opt/rustup \
    MISE_CARGO_HOME=/opt/cargo \
    MISE_PYTHON_COMPILE=0 \
    PATH=/opt/mise/shims:/opt/agents/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
    PASEO_RELAY_ENABLED=false \
    PASEO_SERVICE_PROXY_ENABLED=false
RUN test "$TARGETARCH" = amd64 && apt-get update && apt-get install -y --no-install-recommends \
      build-essential pkg-config cmake ninja-build clang libssl-dev libffi-dev \
      libicu72 zlib1g libkrb5-3 libgssapi-krb5-2 \
      jq ripgrep unzip zip xz-utils file less vim-tiny tmux \
      dnsutils iproute2 iputils-ping netcat-openbsd rsync sqlite3 \
      python3 libgdal-dev gdal-bin libeccodes-dev libeccodes-tools \
      chromium libsecret-1-0 dbus-x11 \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://github.com/jdx/mise/releases/download/v${MISE_VERSION}/mise-v${MISE_VERSION}-linux-x64.tar.gz" -o /tmp/mise.tar.gz \
    && echo "$MISE_SHA256  /tmp/mise.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/mise.tar.gz -C /tmp \
    && install -m 0755 /tmp/mise/bin/mise /usr/local/bin/mise \
    && rm -rf /tmp/mise /tmp/mise.tar.gz
COPY mise.toml /etc/mise/config.toml
RUN mise install --jobs 3 && mise reshim && rm -rf /tmp/mise-cache
RUN npm install --global --prefix /opt/agents \
      "@anthropic-ai/claude-code@$CLAUDE_VERSION" \
      "@openai/codex@$CODEX_VERSION" \
      "@earendil-works/pi-coding-agent@$PI_VERSION" \
    && npm cache clean --force
COPY pi-packages/ /opt/pi-packages/
RUN npm ci --prefix /opt/pi-packages --omit=dev && npm cache clean --force
RUN chown -R 1000:1000 /opt/cargo
# renovate: datasource=npm depName=pnpm
ARG PNPM_VERSION=12.9.1
RUN npm install --global --prefix /opt/agents "pnpm@$PNPM_VERSION" && npm cache clean --force
ARG OP_VERSION=2.39.0
ARG OP_SHA256=6fba7f376b6c6dec49f41b06408930a43ad064cce103c6a2ce5b3d0413a86434
RUN curl -fsSL "https://cache.agilebits.com/dist/1P/op2/pkg/v${OP_VERSION}/op_linux_amd64_v${OP_VERSION}.zip" -o /tmp/op.zip \
    && echo "$OP_SHA256  /tmp/op.zip" | sha256sum -c - \
    && unzip -j /tmp/op.zip op -d /usr/local/bin && chmod 0755 /usr/local/bin/op && rm /tmp/op.zip
COPY agy-release.json /opt/paseo-image/agy-release.json
COPY scripts/install-agy.sh /opt/paseo-image/install-agy.sh
RUN bash /opt/paseo-image/install-agy.sh
COPY scripts/smoke.sh /usr/local/bin/paseo-image-smoke
COPY scripts/entrypoint.sh /usr/local/bin/paseo-dev-entrypoint
COPY config/ /etc/paseo-defaults/
RUN chmod 0755 /usr/local/bin/paseo-image-smoke /usr/local/bin/paseo-dev-entrypoint \
    && chmod -R a+rX /opt/mise /opt/agents \
    && mkdir -p /home/paseo/.cache /workspace \
    && chown -R 1000:1000 /home/paseo /workspace
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="Paseo development workstation with coding agents, language runtimes, and homelab CLIs"
FROM tools AS runtime
ENV DISABLE_AUTOUPDATER=1
USER 1000:1000
WORKDIR /workspace
RUN paseo-image-smoke
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/paseo-dev-entrypoint"]
