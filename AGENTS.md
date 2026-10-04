# Homelab images

Use feature branches and pull requests. Never merge without the user's explicit instruction.
Keep credentials, local agent auth files, and workstation histories out of build contexts.
Keep deployment manifests and all hosting docs, including guides for other clusters, in mitchross/talos-argocd-proxmox. This repo documents the images only; link to talos for deployment.
Pin upstream images by version and digest; pin tool versions. Test images as their runtime user with an empty mounted home.
Migrate images in phases; never remove an old publisher before verifying its replacement.
Do not import anything from programming/work.

Each image directory must have a README. Use short, direct instructions, a small architecture diagram, exact build/test commands, runtime storage and secret requirements, update steps, and known limits. Keep version numbers in their source manifests.

## Migration phases

1. Build and verify Paseo; prepare its Talos deployment through a separate PR.
2. Move Frigate go2rtc and ProxCenter ARM64 build sources/publishers here. Verify replacement publishing before removing old workflows.
3. Preserve archived NInfer build instructions without enabling deployment.
4. Review the remaining personal image inventory. Application builds move only with an explicit source/context strategy; never import `programming/work`.
