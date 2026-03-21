# Glint Doctrine

## Workflow

- Use trunk-based development.
- `main` is trunk.
- Use Graphite (`gt`) for stacked branches and PRs.
- Track planned work in Linear under the `glint` project.
- Install repo hooks with `./scripts/install-hooks.sh`.
- Start each non-trivial branch from one Linear issue.
- Prefer a branch name that includes the Linear issue ID.
- Keep each branch focused on one reviewable concern.
- Prefer `gt c -am "message"` after making changes.
- Use `gt m -a` for follow-up edits on the current branch.
- Use `gt restack` when stack relationships change.
- Submit reviewable slices early with `gt ss`.
- Include a Linear reference in every PR body with `Refs E0D-123`.
- Use `Fixes E0D-123` only on the PR that should close the issue when it lands on `main`.

## Solo Maintainer Policy

- The repo currently relies on workflow discipline rather than branch protection.
- Keep `./scripts/check.sh` green before submitting or merging a branch.
- Merge only after the PR is green locally and in GitHub Actions.
- Use Graphite stacks to keep changes small and auditable even without required approvals.
- Let Graphite retarget stacked PRs after a merge; do not rely on GitHub Actions to delete merged stack branches immediately.
- The label-gated automerge workflow may proactively retarget direct child PRs to the merged PR's base branch before merging so stack promotion stays safe even if the merged branch disappears immediately after. If any direct child PR still targets the soon-to-be-merged branch after that promotion step, the workflow must fail instead of merging.
- Keep stacked PRs linked to their own Linear issue instead of sharing one umbrella issue across the stack.
- Use the `approved[e0da]` label as the merge gate for label-based automerge.
- Use `do-not-merge` to block automerge without rewriting the branch.
- Automerge only applies once a PR targets `main`; stacked child PRs wait until restack promotes them to trunk.
- Treat tags as immutable release identifiers.
- Never move or reuse a published version tag. Cut a new version instead.

## Release Discipline

- The first release target is `0.1.0-alpha.1`.
- Treat prerelease tags as real shipping milestones, not placeholders.
- Keep release notes aligned with the actual shipped behavior.
- Do not describe installable behavior in the README before the binary exists.

## Testing Expectations

- Treat prompt output as the contract.
- Prefer executable specs and golden tests for user-visible behavior.
- Add fixtures for representative Git states before widening implementation.
- Use unit tests for pure parsing and rendering logic.
- Use integration tests for the CLI boundary.

## Design Rules

- Keep the functional core pure where practical.
- Push filesystem, process, and Git I/O to the edges.
- Keep docs short and honest about current state.
- Add new docs only when they protect correctness, reviewability, or onboarding.
