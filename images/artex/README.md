# ARTEX image

Run [ARTEX](https://github.com/BaaRai/ARTEX), an AGPL-3.0 security testing agent platform (Go server, Next.js UI, recon tools).
This image builds upstream's own `Dockerfile` at a pinned release commit. It adds no code and patches nothing.

Upstream publishes release binaries but no image: its Docker Hub job is off and `ghcr.io/baarai/artex` does not exist.

```mermaid
flowchart LR
  Ref[SOURCE_REF + VERSION] --> WF[build-artex.yml]
  Up[BaaRai/ARTEX at SOURCE_REF] -->|upstream Dockerfile, amd64| WF
  WF -->|test with Postgres 16, deployment caps| WF
  WF -->|main only| GHCR[ghcr.io/mitchross/artex:VERSION]
```

Find deployment manifests in [talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox/tree/main/my-apps/development/artex).

## Version pins

| File | Content |
| --- | --- |
| `SOURCE_REF` | Full 40-character commit that upstream tag `v<VERSION>` points at |
| `VERSION` | Upstream release without the `v`, e.g. `0.7.0`. It is also the image tag. |

The workflow checks that `v<VERSION>` (an annotated tag, compared through `^{}`) points at `SOURCE_REF`.
It builds with `ARTEX_VERSION=v<VERSION>`, as upstream's release job does, so the server logs `"version":"<VERSION>"`.
It never overwrites an existing tag, so a rebuild of the same release is not possible without a new tag scheme.

## Build and test

`.github/workflows/build-artex.yml` runs on changes under `images/artex/`, `scripts/test-artex.sh` or the workflow.
Pull requests build and test the image but do not push. A push to `main` publishes `ghcr.io/mitchross/artex:<VERSION>`.

Local build and test, from a checkout of upstream at `SOURCE_REF` and this repository:

```sh
docker build --platform linux/amd64 --build-arg ARTEX_VERSION=v0.7.0 -t artex:local /path/to/ARTEX
bash scripts/test-artex.sh artex:local 0.7.0
```

`scripts/test-artex.sh` starts Postgres 16 (upstream CI's major) and ARTEX the way the talos Deployment does:
root server, all capabilities dropped except `CHOWN DAC_OVERRIDE FOWNER FSETID KILL SETGID SETUID`, no-new-privileges,
`-addr :8787 -proxy 127.0.0.1:8788 -exec-uid 10001 -exec-gid 10001`. It checks:

- `/api/ready` (Postgres ping) and `/api/health` answer;
- the startup config line shows the version, the loopback proxy, `quiet` noise and `/app/keys`;
- the recording proxy does not answer on the container address;
- `/app/data/exec-home` is `10001:10001 700` and `/app/keys/secret.key` is root `600`;
- a command through the drop shim runs as 10001 and cannot read `secret.key`;
- the server is ready again after a restart.

It does not call a model or run a task.

## Runtime contract

| Setting | Requirement |
| --- | --- |
| User | Root server. Agent processes (Bash, shell, custom tools, stdio MCP) drop to 10001:10001. Pass `-exec-uid 10001 -exec-gid 10001` so a failed drop stops the start instead of running agents as root. |
| Capabilities | `CHOWN DAC_OVERRIDE FOWNER FSETID KILL SETGID SETUID`. No `fsGroup`: the server sets owners itself. |
| Ports | `8787` UI and API (`GET /api/ready`, `GET /api/health`). `8788` is the traffic recording proxy; the image's default `CMD` binds it on all addresses, so override it with `-proxy 127.0.0.1:8788`. |
| Storage | `/app/data` (tasks, transcripts, traffic, executor home) and `/app/keys` (`jwt.key`, `secret.key`; set `ARTEX_JWT_KEY_DIR=/app/keys`). Keep `/tmp` from the image: ARTEX checks the sticky bit on its temp directories. |
| Database | Postgres via `ARTEX_PG_DSN`. Upstream tests on Postgres 16. |
| Secrets | `ARTEX_PG_DSN`. Model keys only for paid providers. `secret.key` encrypts stored secrets; losing it loses them. |
| Model | `ARTEX_LLM_PROVIDER=ollama` is keyless OpenAI Chat Completions to `ARTEX_LLM_BASE_URL`; it needs no Ollama daemon. |
| First run | The log prints a one-time setup token for `/setup`. |

## Update

1. Renovate proposes the new release in `VERSION`.
2. Set `SOURCE_REF` to the commit of `v<VERSION>`: `git ls-remote https://github.com/BaaRai/ARTEX.git 'refs/tags/v<VERSION>^{}'`.
3. Read upstream's release notes for database and flag changes, then wait for the build and test.
4. After the owner merges, copy the digest from the `main` run summary into the talos deployment.

## Known limits

- `linux/amd64` only.
- Upstream's final stage uses `python:3.12-slim-bookworm` by tag and installs Playwright, BBOT and recon tools from the network. A rebuild of the same commit can differ.
- The publish job needs write access to the `ghcr.io/mitchross/artex` package. A new package is private; make it public or give the cluster a pull secret before deploying.
