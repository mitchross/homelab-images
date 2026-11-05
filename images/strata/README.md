# Strata CUDA image

Run [Strata](https://github.com/Niko1221/Strata), a llama.cpp-based LLM server with MTP speculative decoding, on RTX 3090 (sm_86) nodes.
This image builds upstream Strata at a pinned commit. It adds no code of its own.

```mermaid
flowchart LR
  Ref[SOURCE_REF + VERSION] --> WF[build-strata.yml]
  Up[Niko1221/Strata at SOURCE_REF] -->|checkout, check STRATA_PORTABLE=ON| WF
  WF -->|upstream Dockerfile, CUDA 13.0, sm_86| GHCR[ghcr.io/mitchross/strata:VERSION]
```

Find deployment manifests in [talos-argocd-proxmox](https://github.com/mitchross/talos-argocd-proxmox/tree/main/my-apps/ai/strata).

## What differs from upstream

- `CUDA_ARCHITECTURES=86`: Ampere only.
- `BUILD_VISION=1` (upstream's default): the image includes the CUDA image encoder `engine/strata-vision`, so the deployment can run with `VISION=yes` and the model can read images.
- `STRATA_COMMIT` and `STRATA_VERSION` build args: upstream's Terminal stage needs the commit (the build context has no `.git`).
- Nothing is patched. Since 0.2.x upstream builds the engine and the image encoder with `-DSTRATA_PORTABLE=ON` (AVX2). The workflow fails if either goes back to `-march=native`, which would bake the CI runner's CPU into the binaries. The GPU node is a Zen+ Threadripper (AVX2, no AVX-512).

Upstream also publishes ready-made images (`ghcr.io/niko1221/strata:<version>-cuda13`) from its signed engine packages. This build stays so the tag, digest and build options are ours.

## Version pins

| File | Content |
| --- | --- |
| `SOURCE_REF` | Full 40-character upstream commit |
| `VERSION` | Image tag: `<strata version>[.<image revision>]-<first 7 of SOURCE_REF>-sm86`, e.g. `0.1.57.0-c3b3f50-sm86` |

`<strata version>` is upstream's `CMakeLists.txt` version padded to four numbers (`0.1.57` -> `0.1.57.0`, `0.1.40.3` stays). The optional fifth number is our image revision: bump it to rebuild the same commit with other build options (`0.1.40.3` -> `0.1.40.3.1` added the image encoder). Drop it when `SOURCE_REF` moves to a new upstream version.

From 0.2.x the image starts through `strata launch` (upstream `docker/entrypoint.sh`), not `setup.py`; see upstream `docs/DOCKER.md` "From the older image" before deploying a bump across that line.

The workflow checks that `VERSION` matches `SOURCE_REF` and upstream's `CMakeLists.txt` version.
It never overwrites an existing tag, so a rebuild needs a new `VERSION`.

## Build

The workflow `.github/workflows/build-strata.yml` runs on changes under `images/strata/`.
Pull requests from this repo build the image but do not push. A push to `main` publishes `ghcr.io/mitchross/strata:<VERSION>`.
The build takes up to a few hours on a hosted runner. There is no runtime test; deployment review is the check.

Local build, from a checkout of upstream at `SOURCE_REF`:

```sh
docker build --platform linux/amd64 --build-arg CUDA_ARCHITECTURES=86 --build-arg BUILD_VISION=1 \
  --build-arg STRATA_COMMIT=$(git rev-parse HEAD) -t strata:local .
```

## Runtime storage and secrets

The image needs no secrets. Model files and the pack cache live on a volume the deployment mounts.

## Update

1. Set `SOURCE_REF` to the new upstream commit and `VERSION` to match.
2. Open a PR here and wait for the build.
3. After the owner merges, copy the digest from the `main` run summary into the talos deployment.

## Known limits

- `linux/amd64`, sm_86 only. Other GPUs need a different `CUDA_ARCHITECTURES` and tag suffix.
- The publish job needs write access to the `ghcr.io/mitchross/strata` package. If the package links to another repo, grant this repo access in the package settings.
