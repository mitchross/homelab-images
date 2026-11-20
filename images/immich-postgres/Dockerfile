# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
# Postgres 19 for Immich: pgvector from PGDG plus VectorChord built from the pgsty fork.
# Upstream ghcr.io/immich-app/postgres stops at Postgres 18; see README "Switch back to upstream".
FROM postgres:19.0-trixie@sha256:bb6e70add742cd868fb62cb3b2f67d1dd2bdd2b65a521e778420748753687c60 AS build
ARG RUST_VERSION=1.100.0
# pgsty/vchord tag 1.3.0
ARG VCHORD_COMMIT=1b35b7a0bc9a71bc82aa4c3396c5545da062d050
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential clang libclang-dev pkg-config curl ca-certificates git postgresql-server-dev-19 \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain "$RUST_VERSION"
ENV PATH=/root/.cargo/bin:$PATH
WORKDIR /src
RUN git init -q . \
    && git fetch -q --depth 1 https://github.com/pgsty/vchord.git "$VCHORD_COMMIT" \
    && git checkout -q FETCH_HEAD
RUN PG_CONFIG=/usr/lib/postgresql/19/bin/pg_config make build \
    && make PG_CONFIG=/usr/lib/postgresql/19/bin/pg_config DESTDIR=/out install

FROM postgres:19.0-trixie@sha256:bb6e70add742cd868fb62cb3b2f67d1dd2bdd2b65a521e778420748753687c60
ARG PGVECTOR_VERSION=0.8.7-1.pgdg13+2
RUN apt-get update \
    && apt-get install -y --no-install-recommends "postgresql-19-pgvector=$PGVECTOR_VERSION" \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/ /
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.description="Postgres 19 with pgvector and VectorChord for Immich"
# VectorChord must be preloaded or CREATE EXTENSION vchord fails.
CMD ["postgres", "-c", "shared_preload_libraries=vchord.so"]
