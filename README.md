# Homelab images

Build definitions for mitchross's shared development environments and customized
upstream software. Deployment manifests and ExternalSecrets belong in
[mitchross/talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox).
Never put credentials or workstation histories in this repository or an image.

## Paseo development workstation

`images/paseo-dev` extends the official pinned Paseo image for **linux/amd64**.
It includes Claude Code, Codex, Pi, Antigravity CLI, Node/npm, Bun, Python/uv,
.NET, Rust, Go, Java/Maven/Gradle, Chromium, GDAL/ecCodes, and the homelab CLIs.
React/Expo and project Python packages remain repository dependencies.

```sh
docker build -t paseo-dev:local images/paseo-dev
bash scripts/test-paseo.sh paseo-dev:local
```

The process runs as 1000:1000. Tools live in `/opt`, not the persistent home.
Mount `/home/paseo` and `/workspace` on writable persistent storage. The daemon
refuses to start unless `PASEO_PASSWORD` is supplied; relay and service publishing
are disabled by default. Forward HTTP and WebSockets through HTTPS.

Provide secrets at runtime through ESO: daemon password, provider credentials,
Git credentials, and separately authorized Omni/Kubernetes/Proxmox access.
Fresh provider logins persist in the home volume. The image contains no copied
local authentication or history. Pi defaults include the workstation model definitions and pinned extensions.
Paseo uses its bundled Node runtime; development commands use Node 24.
Claude auto-updates are disabled so image updates own its version.
Pi uses the in-cluster LiteLLM service; existing home settings are preserved on upgrade.
Supply `LITELLM_API_KEY` (and optionally `OPENROUTER_API_KEY`) at runtime.
Desktop-only bridges and local authentication are not copied.

The Docker CLI needs a separately configured remote Docker engine to build or
run containers. iOS/watch builds need a Mac runner. Antigravity requires its own
login and Paseo drives it in full-access mode; its interactive permission and
transcript replay limitations still apply.

## Personal agent configuration

Keep personal skills, rules, agent definitions, and sanitized plugin/MCP manifests
in a separate private configuration repository. Do not copy workstation `.claude`,
`.codex`, or `.pi` directories into this public build context.

On first deployment, restore the reviewed bundle into the persistent home and
recreate skill links relative to `/home/paseo/.agents/skills`. Rewrite local paths
and inspect hooks before enabling them. Install plugins from their recorded sources
and versions rather than copying caches. Project `CLAUDE.md`, `AGENTS.md`, and
repository-scoped skills arrive with each project checkout.

Supply MCP credentials through runtime secrets or fresh authentication. Desktop
bridges and app-hosted connectors require separate compatibility checks; a copied
skill does not provision its tools. Preserve existing settings during subsequent
image upgrades. This configuration migration remains a deployment prerequisite.

## Optional Paseo plugins

The image does not enable third-party Paseo plugins. Provider support is already
built in; Pi extension packages are a separate layer. Review and opt into these
on the deployed daemon after its baseline works:

| Plugin | Use |
| --- | --- |
| [Shared Browser](https://github.com/omercnet/paseo-plugins/tree/main/paseo-shared-browser) | Share a workspace browser between agents and your phone; requires Node 24 and a prepared Chromium runtime |
| [PR Radar](https://github.com/omercnet/paseo-plugins/tree/main/pr-radar) | Track workspace PRs and checks; requires authenticated `gh` |
| [Agent Monitor](https://github.com/omercnet/paseo-plugins/tree/main/agent-monitor) | Triage agents across workspaces |

Plugins execute with the daemon user's access to credentials and infrastructure.
Pin and test selected versions; directory catalog checks are not a source audit.

## Local builds on CachyOS

Run `bash scripts/publish-paseo-local.sh` from a clean committed checkout. It builds
with the local Docker cache, runs the same fresh-home tests as CI, and pushes a
unique `local-<commit>-<timestamp>` candidate to GHCR. Your GitHub CLI identity needs
package write access. Registry login uses a temporary Docker configuration.

Subsequent local builds reuse layers; pushes upload only missing registry layers.
The command prints a digest for the deployment PR and never updates `main`.
Local Docker cache and GitHub Actions cache are separate. A local push alone does
not warm GitHub's build cache; Actions retains its own cache after a successful run.

## Updates and publishing

Fork pull requests build and test without publishing. Same-repository PRs use
their branch push check to avoid duplicate builds. Trusted repository pushes
publish `ghcr.io/mitchross/paseo-dev:sha-<full-commit>-<run-id>-<attempt>` after tests pass; branch
images are candidates, not a production promotion. Pin the resulting digest in
a separate infrastructure PR. Main also publishes a rolling `main` tag. Pin `:main@sha256:...` in GitOps so
Renovate proposes digest updates. Never merge or deploy automatically.

Renovate manages base images, Actions and mise tool pins once installed for this
repository. Agent versions are tracked Dockerfile arguments; Antigravity's release URL
and SHA512 are recorded in `agy-release.json` from Google's release manifest.
Update the Antigravity manifest explicitly. The mise bootstrap and 1Password CLI
version/checksum pairs require manual updates together; Renovate tracks the tools
installed by mise. Coding agent updates are grouped weekly. A weekly workflow rebuilds OS packages; re-run it for urgent security fixes
and record the new resulting digest in the deployment PR. A rollback uses the
previous digest; back up home/workspace before upgrades that change stored data.

## Migration phases

1. Build and verify Paseo; prepare its Talos deployment through a separate PR.
2. Move Frigate go2rtc and ProxCenter ARM64 build sources/publishers here. Verify
   replacement publishing before removing old workflows.
3. Preserve archived NInfer build instructions without enabling deployment.
4. Review the remaining personal image inventory. Application builds move only
   with an explicit source/context strategy; never import `programming/work`.
