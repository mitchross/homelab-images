# syntax=docker/dockerfile:1
FROM python:3.12.15-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 AS sdk
ARG TARGETARCH
ARG AGORA_PYTHON_VERSION=2.4.9
ARG AGORA_PYTHON_URL=https://files.pythonhosted.org/packages/33/4d/715e0c325e42ff20484729c1503ac5d89097d31abd2b9db27f48bcac6eec/agora_python_server_sdk-2.4.9.tar.gz
ARG AGORA_PYTHON_SHA256=3f9453ce4730c1b9db86e56ea9b96713ffc576060b357d9bf0de8f65b473031e
ARG AGORA_SDK_URL=https://download.agora.io/sdk/release/agora_rtc_sdk_x86_64-linux-gnu-v4.4.32.174_28020_SERVER_20260601_1240_1144448_20251021_1427-3a.zip
ARG AGORA_SDK_SHA256=66f8a30dc75bb4f50a0597b52445c2b197bbc1970cd632262a24cdffe39b9130
ARG GO2RTC_VERSION=1.9.14
ARG GO2RTC_SHA256=32d616af226bd731678ffde328b94cfb94e30339bfefc469cfb76323144615a6
RUN test "$TARGETARCH" = amd64 && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "$AGORA_PYTHON_URL" -o /tmp/python-sdk.tar.gz \
    && echo "$AGORA_PYTHON_SHA256  /tmp/python-sdk.tar.gz" | sha256sum -c - \
    && mkdir /opt/agora \
    && tar -xzf /tmp/python-sdk.tar.gz -C /opt/agora --strip-components=1 \
    && curl -fsSL "$AGORA_SDK_URL" -o /tmp/native-sdk.zip \
    && echo "$AGORA_SDK_SHA256  /tmp/native-sdk.zip" | sha256sum -c - \
    && unzip -q /tmp/native-sdk.zip -d /opt/agora/agora \
    && printf '%s' "$AGORA_SDK_URL" > /opt/agora/agora/version.txt \
    && chmod -R a+rX /opt/agora/agora \
    && rm -rf /opt/agora/agora/agora_sdk/include
# Copy the wrapper directly; its setup.py downloads an unverified SDK during installation.
RUN curl -fsSL "https://github.com/AlexxIT/go2rtc/releases/download/v${GO2RTC_VERSION}/go2rtc_linux_amd64" -o /usr/local/bin/go2rtc \
    && echo "$GO2RTC_SHA256  /usr/local/bin/go2rtc" | sha256sum -c - \
    && chmod 0755 /usr/local/bin/go2rtc

FROM python:3.12.15-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 AS runtime
ARG FFMPEG_VERSION=7:5.1.9-0+deb12u1
ARG TINI_VERSION=0.19.0-1+b3
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates "ffmpeg=$FFMPEG_VERSION" "tini=$TINI_VERSION" \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/wyze && chown 1000:1000 /home/wyze
COPY --from=sdk /opt/agora/agora /opt/agora/agora
COPY --from=sdk /usr/local/bin/go2rtc /usr/local/bin/go2rtc
COPY protocol.py receiver.py /opt/wyze-lake/
ENV PYTHONPATH=/opt/agora:/opt/wyze-lake \
    LD_LIBRARY_PATH=/opt/agora/agora/agora_sdk \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/home/wyze
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="Native Linux Wyze Cam Pan v4 Lake video receiver with RTSP output"
USER 1000:1000
WORKDIR /opt/wyze-lake
EXPOSE 8554/tcp
HEALTHCHECK --interval=15s --timeout=5s --start-period=90s CMD ["python3", "/opt/wyze-lake/receiver.py", "--health"]
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/wyze-lake/receiver.py"]
