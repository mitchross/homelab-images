# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183
# Mainline llama.cpp server for RTX 3090 (sm_86), built from SOURCE_REF. Nothing is patched.
ARG LLAMA_COMMIT
ARG LLAMA_BUILD_NUMBER

FROM node:24.22.3-trixie@sha256:6e5d4c38403930b420404f190be8563396dca2bd156a6cb4722707b0efcf6fc1 AS source
ARG LLAMA_COMMIT
WORKDIR /src
RUN test -n "$LLAMA_COMMIT" \
    && git init -q . \
    && git fetch -q --depth 1 https://github.com/ggml-org/llama.cpp.git "$LLAMA_COMMIT" \
    && git checkout -q FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "$LLAMA_COMMIT"

# The chat UI is built from source so the build never downloads prebuilt assets.
FROM node:24.22.3-trixie@sha256:6e5d4c38403930b420404f190be8563396dca2bd156a6cb4722707b0efcf6fc1 AS web
ARG LLAMA_BUILD_NUMBER
WORKDIR /app/ui/apps/chat
COPY --from=source /src/ui/apps/chat/package.json /src/ui/apps/chat/package-lock.json ./
RUN npm ci
COPY --from=source /src/ui/apps/chat/ ./
COPY --from=source /src/ui/lib/ui/package.json /app/ui/lib/ui/package.json
COPY --from=source /src/ui/lib/ui/src/lib/ /app/ui/lib/ui/src/lib/
COPY --from=source /src/ui/lib/voice/src/ /app/ui/lib/voice/src/
RUN LLAMA_BUILD_NUMBER="b$LLAMA_BUILD_NUMBER" npm run build

FROM nvidia/cuda:13.0.3-devel-ubuntu24.04@sha256:b7ae301dea2c162444795462ce17a05f6a516e5a75944b57af5b88540a1a2266 AS build
ARG LLAMA_COMMIT
ARG LLAMA_BUILD_NUMBER
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc-14 g++-14 build-essential cmake git libssl-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*
ENV CC=gcc-14 CXX=g++-14 CUDAHOSTCXX=g++-14
WORKDIR /src
COPY --from=source /src/ ./
COPY --from=web /app/ui/apps/chat/dist ui/apps/chat/dist
# CPU backends load at runtime, so one image runs on any x86-64 node (the GPU node is AVX2 Zen+).
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release \
        -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 \
        -DGGML_NATIVE=OFF -DGGML_BACKEND_DL=ON -DGGML_CPU_ALL_VARIANTS=ON \
        -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_USE_PREBUILT_UI=OFF \
        -DLLAMA_BUILD_NUMBER="$LLAMA_BUILD_NUMBER" -DLLAMA_BUILD_COMMIT="$(echo "$LLAMA_COMMIT" | cut -c1-7)" \
        -DCMAKE_EXE_LINKER_FLAGS=-Wl,--allow-shlib-undefined \
    && cmake --build build --config Release -j"$(nproc)"
# Fail unless the CUDA backend holds sm_86 code and nothing else.
RUN cuobjdump --list-elf build/bin/libggml-cuda.so | grep -q 'sm_86' \
    && ! cuobjdump --list-elf build/bin/libggml-cuda.so | grep -v 'sm_86' | grep -q 'sm_'
RUN mkdir -p /out \
    && find build -name '*.so*' -exec cp -P {} /out/ \; \
    && cp build/bin/llama-server build/bin/llama-cli build/bin/llama-bench /out/

FROM nvidia/cuda:13.0.3-runtime-ubuntu24.04@sha256:76f46f3e649824ebd3685d3d86c42b0ea62af04f59242f419f56cd5804a72efb
ARG LLAMA_COMMIT
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libssl3t64 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/llama /models \
    && chown 65532:65532 /home/llama /models
COPY --from=build /out/ /app/
ENV PATH=/app:$PATH \
    HOME=/home/llama \
    LD_LIBRARY_PATH=/usr/local/nvidia/lib64:/usr/local/nvidia/lib:/app \
    LLAMA_ARG_HOST=0.0.0.0 \
    LLAMA_ARG_PORT=8080
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.url="https://github.com/ggml-org/llama.cpp" \
      org.opencontainers.image.revision="$LLAMA_COMMIT" \
      org.opencontainers.image.description="Mainline llama.cpp server, CUDA 13.0, sm_86"
USER 65532:65532
WORKDIR /home/llama
EXPOSE 8080
HEALTHCHECK CMD ["curl", "-fsS", "http://localhost:8080/health"]
ENTRYPOINT ["/app/llama-server"]
