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

## Review Rule

Generated fixture changes are not automatically accepted as product truth.
Review the diff and decide whether a changed upstream behavior belongs in the
`glint` compatibility contract before updating implementation or specs.
