# Homelab images

Keep credentials, local agent auth files, and workstation histories out of build contexts.
Keep deployment manifests and all hosting docs, including guides for other clusters, in mitchross/talos-argocd-proxmox. This repo documents the images only; link to talos for deployment.
Pin upstream images by version and digest; pin tool versions. Test images as their runtime user with an empty mounted home.
Migrate images in phases; never remove an old publisher before verifying its replacement.
Do not import anything from programming/work.

Each image directory must have a README. Use short, direct instructions, a small architecture diagram, exact build/test commands, runtime storage and secret requirements, update steps, and known limits. Keep version numbers in their source manifests.

## Git workflow

This block is the same in every repo. Other rules in this file may add to it, never relax it.

- Work on a feature branch and open a pull request. Never push to the default branch.
- Never merge a pull request. The owner merges after review.
- Keep one writer per checkout. A lone agent may use the main checkout on a feature branch. When another agent or task uses that checkout, work in a worktree.
- Use your tool's own worktree feature: Claude Code `--worktree` (`.claude/worktrees/`), Hermes `-w` or `/worktree new` (`.worktrees/`), Codex app worktrees (`$CODEX_HOME/worktrees`). Cloud agents use their own sandbox and coordinate only through branches and pull requests.
- Create a worktree by hand only under `~/.local/share/agent-worktrees/<repo>/<task>/`, never as a sibling folder next to the repo.
- Reuse the task's worktree for follow-ups. Before you resume an old worktree, check its branch and PR state, and read the repo's `AGENTS.md` from the default branch (`git show origin/HEAD:AGENTS.md`).
- When the PR is merged or closed, remove your worktree with the tool's exit prompt or `git worktree remove <path>`. Keep and report a worktree that has uncommitted, untracked or unpushed work.
- Never run `git worktree remove --force`, `git reset --hard`, `git clean` or `rm -rf` on a checkout, and never delete a branch, unless the owner asks. Never force-push a branch another agent or person works on.

## Migration phases

1. Build and verify Paseo; prepare its Talos deployment through a separate PR.
2. Move Frigate go2rtc and ProxCenter ARM64 build sources/publishers here. Verify replacement publishing before removing old workflows.
3. Preserve archived NInfer build instructions without enabling deployment.
4. Review the remaining personal image inventory. Application builds move only with an explicit source/context strategy; never import `programming/work`.
