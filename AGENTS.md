# Homelab images

Use feature branches and pull requests. Never merge without the user's explicit instruction.
Keep credentials, local agent auth files, and workstation histories out of build contexts.
Keep deployment manifests in mitchross/talos-argocd-proxmox.
Pin upstream images by version and digest; pin tool versions. Test images as their runtime user with an empty mounted home.
Migrate images in phases; never remove an old publisher before verifying its replacement.
Do not import anything from programming/work.
