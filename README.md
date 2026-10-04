# Homelab images

Build definitions for mitchross's shared development environments and customized
upstream software. This cluster's deployment manifests and ExternalSecrets belong in
[mitchross/talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox).
`deploy/` holds generic examples for other clusters.
Never put credentials or workstation histories in this repository or an image.

## Images

| Image | Guide |
| --- | --- |
| Paseo development workstation | [Build, run, configure, and update](images/paseo-dev/README.md) |
| Paseo on another Kubernetes cluster | [Plain manifests, step by step](deploy/kubernetes/paseo/README.md) |

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

## Migration phases

1. Build and verify Paseo; prepare its Talos deployment through a separate PR.
2. Move Frigate go2rtc and ProxCenter ARM64 build sources/publishers here. Verify
   replacement publishing before removing old workflows.
3. Preserve archived NInfer build instructions without enabling deployment.
4. Review the remaining personal image inventory. Application builds move only
   with an explicit source/context strategy; never import `programming/work`.
