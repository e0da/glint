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

- Protect `main` in GitHub with required checks instead of relying only on workflow discipline.
- Keep `./scripts/check.sh` green before submitting or merging a branch.
- Merge only after the PR is green locally and GitHub shows every required check green.
- Use Graphite stacks to keep changes small and auditable even without required approvals.
- Use `./scripts/protect-main.sh` to reapply the live `main` branch protection when the repo is recreated or settings drift.
- Keep stacked PRs linked to their own Linear issue instead of sharing one umbrella issue across the stack.
- Require `fmt, clippy, test, build` and `merge-readiness/e0da` on `main`.
- The `merge-readiness/e0da` status stays pending on `main`-targeting PRs until at least one label matching `approved[...]` is present.
- Use `approved[e0da]` as the current solo-maintainer approval label; the first rule intentionally accepts any single `approved[...]` label.
- Use `do-not-merge` to push `merge-readiness/e0da` back to pending without rewriting the branch.
- Stacked child PRs stay outside the readiness gate until Graphite promotion retargets them to `main`.
- The default Graphite loop is: stack with `gt ss`, review bottom-up, then use Graphite `Merge when ready` on the lowest PR once it targets `main` and GitHub shows the required checks green.
- Do not use `Merge when ready` on child PRs that still target another stack branch; let Graphite promote them to `main` first.
- For the solo-maintainer flow, the buttery path is: push the branch, wait for CI, add `approved[e0da]` when you want it merge-eligible, then click `Merge when ready`.
- Treat tags as immutable release identifiers.
- Never move or reuse a published version tag. Cut a new version instead.

## Release Discipline

- The first release target is `0.1.0-alpha.1`.
- Treat prerelease tags as real shipping milestones, not placeholders.
- Keep release notes aligned with the actual shipped behavior.
- Do not describe installable behavior in the README before the binary exists.

## Testing Expectations

- Treat prompt output as the contract.
- Prefer capturing compatibility behavior as executable fixtures before widening
  implementation.
- Prefer executable specs and golden tests for user-visible behavior.
- Add fixtures for representative Git states before widening implementation.
- Use unit tests for pure parsing and rendering logic.
- Use integration tests for the CLI boundary.
- Measure prompt latency in two layers: direct invocation cost and integrated
  shell behavior.
- Keep latency checks tied to an explicit invalidation strategy, not only raw
  command runtime.

## Design Rules

- Keep the functional core pure where practical.
- Push filesystem, process, and Git I/O to the edges.
- Keep docs short and honest about current state.
- Add new docs only when they protect correctness, reviewability, or onboarding.
- Treat command execution policy and invalidation strategy as product
  architecture, not shell glue.
