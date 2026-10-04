# Homelab images

Container images for mitchross's homelab. Each image has its own README.

| Image | README |
| --- | --- |
| `ghcr.io/mitchross/paseo-dev`: Paseo with coding agents and dev tools | [images/paseo-dev](images/paseo-dev/README.md) |

| Folder | Holds |
| --- | --- |
| `images/<name>/` | Dockerfile, config, and README for one image |
| `deploy/` | Generic deployment examples for other clusters |
| `scripts/` | Image tests |

Point a coding agent at [`llms.txt`](llms.txt) for raw links to every guide and manifest.
