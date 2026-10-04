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
Supply `LITELLM_API_KEY` (and optionally `OPENROUTER_API_KEY`) at runtime.
Desktop-only bridges and local authentication are not copied.

The Docker CLI needs a separately configured remote Docker engine to build or
run containers. iOS/watch builds need a Mac runner. Antigravity requires its own
login and Paseo drives it in full-access mode; its interactive permission and
transcript replay limitations still apply.

## Updates and publishing

Pull requests build and test without publishing. Trusted repository pushes also
publish `ghcr.io/mitchross/paseo-dev:sha-<full-commit>-<run-id>-<attempt>` after tests pass; branch
images are candidates, not a production promotion. Pin the resulting digest in
a separate infrastructure PR. Never merge or deploy automatically.

Renovate manages base images, Actions and mise tool pins once installed for this
repository. Agent versions are tracked Dockerfile arguments; Antigravity's release URL
and SHA512 are recorded in `agy-release.json` from Google's release manifest.
Update the Antigravity manifest explicitly. A weekly workflow rebuilds OS packages; re-run it for urgent security fixes
and record the new resulting digest in the deployment PR. A rollback uses the
previous digest; back up home/workspace before upgrades that change stored data.

## Migration phases

1. Build and verify Paseo; prepare its Talos deployment through a separate PR.
2. Move Frigate go2rtc and ProxCenter ARM64 build sources/publishers here. Verify
   replacement publishing before removing old workflows.
3. Preserve archived NInfer build instructions without enabling deployment.
4. Review the remaining personal image inventory. Application builds move only
   with an explicit source/context strategy; never import `programming/work`.
