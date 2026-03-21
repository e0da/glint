# Compatibility Harness

This directory holds the upstream-compatibility workflow for `glint`.

## Goals

- Capture observed `zsh-git-prompt` behavior in a clean environment.
- Store the captured behavior as machine-readable fixtures.
- Verify `glint` against those fixtures in normal local and CI test runs.
- Keep `glint` implementation independent from upstream shell code once the
  behavioral contract is captured.

## Split

- `compat/generate-upstream-fixtures.sh`
  - Containerized, expensive, updates fixture files from upstream behavior.
- `cargo test --test compat_fixtures`
  - Cheap, local, runs `glint` against checked-in fixtures.

## Fixture Format

Fixtures live in `compat/fixtures/*.json`.

Each file contains:

- metadata about the upstream ref and generator run
- ordered setup operations for synthetic repos
- theme/env overrides
- expected stdout for `glint`

The verifier treats fixture files as the contract surface. The generator is
allowed to update them. Normal CI should only verify them.

This keeps the workflow spec-first:

- observe upstream behavior
- review and accept the fixture diff as contract
- implement `glint` natively in Rust against that contract

## Generator Workflow

1. Build the container from `compat/Dockerfile`.
2. Clone the pinned upstream repo inside the container.
3. Create synthetic repos for each compatibility case.
4. Invoke upstream `git_super_status` under controlled theme variables.
5. Write JSON fixtures into `compat/fixtures/`.

The wrapper defaults `UPSTREAM_SCRIPT` to `zshrc.sh`, which matches the current
upstream `master` layout. Override it only when targeting a different upstream
script path deliberately.

## Generator Language Decision

Keep the upstream-capture generator in Python for now.

Current rationale from the 2026-03-21 investigation:

- the generator is isolated to the expensive refresh path, not the normal
  Rust runtime path
- the current implementation is stdlib-only and already fits the container
  model cleanly
- measured cost is dominated by external `git` and `zsh` subprocess work,
  not by Python startup or execution
- most of the script's size is compatibility-case declaration rather than
  complex Python-specific logic

Revisit the language only if the harness develops real maintenance pain or a
clear workflow need. Treat any future rewrite as a maintainability decision,
not a performance project.

## Base Image Decision

Keep the compatibility harness on `ubuntu:24.04` for now.

Current rationale from the 2026-03-21 investigation:

- Ubuntu and Debian slim produced the same generated fixture corpus in the
  current harness shape
- Alpine built smaller and faster, but changed the generated fixture corpus
- for a compatibility-capture path, stable observable behavior matters more
  than image size alone
- Debian slim remains a credible future option, but it does not currently
  justify churn on its own

Revisit the base image only if a stronger operational need appears or the
harness changes enough to justify re-running the comparison.

## Review Rule

Generated fixture changes are not automatically accepted as product truth.
Review the diff and decide whether a changed upstream behavior belongs in the
`glint` compatibility contract before updating implementation or specs.
