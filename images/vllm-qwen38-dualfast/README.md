# vLLM Qwen3.8 dual-fast

`vllm/vllm-openai` → build-time club-3090 patches → stock `vllm serve` entrypoint.

The base version/digest is in `Dockerfile`; the published tag is in `VERSION`.
The unmodified vendored patches come from [club-3090](https://github.com/noonghunna/club-3090)
at the commit in `SOURCE_REF`, under Apache-2.0 (`patches/LICENSE`). Their original
paths are `models/qwen3.6-27b/vllm/patches/vllm-pr48375-mamba-drop-eagle-block`
and `models/qwen3.8-27b/vllm/patches/{vllm-humming-w4a8,vllm-flashinfer-decode-pin}`.
Also vendored from that same commit: Qwen3.8's `vllm-effort-budget` (B),
`vllm-default-thinking-budget` (D), `scripts/lib/effort_budget.py`, and
`qwen38-reasoning-effort-template` with its `PROVENANCE.md`.

B then D are installed before the existing patches, at build time only. Runtime
must set `CLUB3090_REASONING_EFFORT_BUDGETS` and
`CLUB3090_DEFAULT_THINKING_TOKEN_BUDGET`; build-time exports do not persist.
For low=4096, medium=16384, xhigh=32768 and default effort medium, the upstream
`effort_budget.py shell-env --engine vllm --default-effort medium --low 4096 --medium 16384 --xhigh 32768`
emits the map `{"high":32768,"low":4096,"max":32768,"medium":16384,"minimal":4096,"xhigh":32768}`
and floor `16384`. Kubernetes supplies these two values directly; no wrapper is needed.
An explicit request budget wins; upstream's sampled top-k-off safety bypass remains.

The baked template is `/etc/club3090/qwen38-reasoning-effort-template/chat_template.jinja`.
Pass it via `--chat-template` with default effort medium. It maps high/max to xhigh
and minimal to low; the unchanged upstream provenance also documents tool-key
sorting and in-place system messages. vLLM's `--reasoning-parser qwen3`
already creates `ReasoningConfig` and derives `<think>`/`</think>` token IDs;
no additional `--reasoning-config` is required. Smoke checks both installed AST
hooks, effort aliases, explicit-budget precedence, floor fallback and template rendering.

vLLM v0.34.0 removed Marlin W4A8. W4A8 now runs on humming: serve with
`--quantization humming` and `VLLM_HUMMING_INPUT_QUANT_CONFIG={"dtype":"int8"}`.
The humming patch fixes AutoRound loading (vllm#68194) and double weight memory
(vllm#68195), and logs `[humming-w4a8] effective activations a_dtype=int8` at boot.
Never set `VLLM_MARLIN_INPUT_DTYPE`; v0.34 refuses to start with it. The other
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
`VERSION` must start with the base tag; CI fails otherwise so a bump can't overwrite an old tag.
For a patch update, re-vendor the patch directories, helper and template from one reviewed commit,
update `SOURCE_REF` and the revision label, bump `VERSION`, and run build/smoke.
Patch-anchor drift fails the build. CPU smoke does not prove GPU inference,
vision correctness, concurrent long-context capacity or MTP stability.
