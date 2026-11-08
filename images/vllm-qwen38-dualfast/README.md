# vLLM Qwen3.8 dual-fast

`vllm/vllm-openai` → build-time club-3090 patches → stock `vllm serve` entrypoint.

The base version/digest is in `Dockerfile`; the published tag is in `VERSION`.
The unmodified vendored patches come from [club-3090](https://github.com/noonghunna/club-3090)
at the commit in `SOURCE_REF`, under Apache-2.0 (`patches/LICENSE`). Their original
paths are `models/qwen3.6-27b/vllm/patches/{w4a8-int8-act,vllm-pr48375-mamba-drop-eagle-block}`
and `models/qwen3.8-27b/vllm/patches/vllm-flashinfer-decode-pin`.

W4A8 threads the int8 input dtype and folds negative AutoRound scales. The other
patches prepare a future MTP A/B; speculation remains off in production. The
FlashInfer patch is decode-only (`FI_PINQ_LIB_ALL=0`). Its package path is found
without importing GPU-dependent FlashInfer code during a CPU-only build.

```sh
docker build -t vllm-qwen38-dualfast images/vllm-qwen38-dualfast
docker run --rm --entrypoint python3 -v dualfast-smoke-home:/root vllm-qwen38-dualfast /opt/dualfast/smoke.py
```

CI builds on pull requests, checks the installed patches and imports vLLM, then
publishes the tested version to `ghcr.io/mitchross/vllm-qwen38-dualfast` on main.
No credentials or model files are baked in. Runtime needs NVIDIA GPUs, mounted
model files and writable compiler caches; see the [GitOps runbook](https://github.com/mitchross/talos-argocd-proxmox/blob/main/my-apps/ai/vllm/README.md).

Renovate proposes base-image bumps for manual review; patches must still apply.
For a patch update, re-vendor all three directories from one reviewed commit,
update `SOURCE_REF` and the revision label, bump `VERSION`, and run build/smoke.
Patch-anchor drift fails the build. CPU smoke does not prove GPU inference,
vision correctness, concurrent long-context capacity or MTP stability.
