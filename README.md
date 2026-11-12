# Homelab images

Container images for mitchross's homelab. Each image has its own README.

| Image | README |
| --- | --- |
| Hermes agent with coding agents and cluster CLIs | [Build, test, storage, updates](images/hermes-dev/README.md) |
| `ghcr.io/mitchross/wyze-lake`: native Cam Pan v4 video to RTSP | [images/wyze-lake](images/wyze-lake/README.md) |
| `ghcr.io/mitchross/strata`: Strata LLM server, CUDA sm_86 | [images/strata](images/strata/README.md) |
| `ghcr.io/mitchross/fio`: pinned fio storage benchmark with jq | [images/fio](images/fio/README.md) |

| Folder | Holds |
| --- | --- |
| `images/<name>/` | Dockerfile, config, and README for one image |
| `scripts/` | Image tests |

Deployment docs live in [talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox/tree/main/docs). Each image README links to its guide.
