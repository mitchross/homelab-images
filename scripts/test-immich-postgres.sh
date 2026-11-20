#!/usr/bin/env bash
set -euo pipefail
image=${1:?image required}
name=immich-postgres-test-$$
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
# Run as the postgres uid with an empty data volume, like the cluster pod.
docker run -d --name "$name" --user 999:999 --tmpfs /var/lib/postgresql:uid=999,gid=999 \
  -e POSTGRES_USER=immich -e POSTGRES_PASSWORD=test -e POSTGRES_DB=immich "$image" >/dev/null
for _ in $(seq 60); do
  docker exec "$name" psql -U immich -d immich -Atc 'select 1' >/dev/null 2>&1 && break
  sleep 1
done
# The index options are the ones Immich uses for clip_index and face_index.
docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U immich -d immich -At >/tmp/immich-postgres-test.out <<'SQL'
create extension vchord cascade;
select 'server ' || current_setting('server_version_num');
select extname || ' ' || extversion from pg_extension where extname in ('vector', 'vchord') order by 1;
create table t (id int primary key, e vector(512));
insert into t select g, (select array_agg(random())::real[] from generate_series(1, 512) where g is not null)::vector(512) from generate_series(1, 500) g;
create index t_idx on t using vchordrq (e vector_cosine_ops) with (options = '
residual_quantization = false
[build.internal]
lists = [1]
spherical_centroids = true
build_threads = 4
sampling_factor = 1024
');
set enable_seqscan = off;
set vchordrq.probes = 1;
select 'nearest ' || id from t order by e <=> (select e from t where id = 7) limit 1;
SQL
cat /tmp/immich-postgres-test.out
grep -q '^server 19' /tmp/immich-postgres-test.out
grep -q '^vchord ' /tmp/immich-postgres-test.out
grep -q '^vector ' /tmp/immich-postgres-test.out
grep -qx 'nearest 7' /tmp/immich-postgres-test.out
