# Homelab images

Container images for mitchross's homelab. Each image has its own README.

| Image | README |
| --- | --- |
| `ghcr.io/mitchross/paseo-dev`: Paseo with coding agents and dev tools | [images/paseo-dev](images/paseo-dev/README.md) |
| `ghcr.io/mitchross/wyze-lake`: native Cam Pan v4 video to RTSP | [images/wyze-lake](images/wyze-lake/README.md) |

| Folder | Holds |
| --- | --- |
| `images/<name>/` | Dockerfile, config, and README for one image |
| `scripts/` | Image tests |

Deployment docs live in [talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox/tree/main/docs). Each image README links to its guide.
