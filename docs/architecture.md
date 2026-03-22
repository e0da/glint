# Glint Architecture

## Purpose

This document explains the current `glint` execution model and the performance
strategy that should guide post-alpha work.

The product contract remains the prompt output shape and compatibility fixtures.
Performance work is only valuable if it preserves that observable behavior.

## Current Runtime Path

Today `glint` is a single-shot CLI:

1. read theme overrides from the process environment
2. invoke `git status --porcelain=v2 --branch`
3. parse the status output into a narrow Rust status model
4. render the prompt segment

Detached HEAD uses one extra `git rev-parse --short HEAD` call so the rendered
hash respects Git's configured abbreviation length.

This keeps the implementation simple and already improves substantially on the
original upstream Python path, which shells out multiple times per refresh.

## Compatibility Capture Path

The upstream compatibility-capture harness remains a separate, containerized
Python workflow in `compat/`.

That is an intentional choice for now.

The 2026-03-21 investigation found that this path is dominated by external
`git` and `zsh` subprocess orchestration rather than host-language runtime
cost. The current generator is also stdlib-only and mostly expresses fixture
cases, not complex Python-specific logic.

In practice, this means:

- keep the expensive upstream-capture path isolated from the Rust runtime path
- do not treat a Python-to-TypeScript rewrite as a performance lever
- revisit the language only if maintainability or workflow costs become real
  enough to justify the rewrite
- if TypeScript is ever reconsidered for this path, evaluate it as a workflow
  choice first

The harness also stays on an Ubuntu base image for now.

The 2026-03-21 container-base investigation found that Alpine changed the
generated fixture corpus, while Ubuntu and Debian slim matched each other.
That makes image size a secondary concern here: the compatibility harness
should prefer distro behavior that stays boring and stable over the smallest
possible container footprint.

## Measured Direction

The direct-invocation benchmarks from 2026-03-21 point to three conclusions:

- one `git status --porcelain=v2 --branch` call is already close to the lower
  bound for the current CLI shape
- replacing that with several smaller Git plumbing commands is slower, not
  faster
- the remaining large win is avoiding unnecessary recomputation, not splitting
  the same work across more subprocesses

In other words, "more strategic" should mean "run less often" before it means
"run different Git commands."

## Repeatable Benchmark Harness

The repo now carries a small latency harness so performance decisions can be
rechecked against the same corpus instead of relying on one-off numbers.

Use `./scripts/benchmark.sh` to regenerate the benchmark corpus in
`tmp/benchmark-corpus/` and record fresh results in `tmp/benchmark-results/`.

The corpus intentionally stays small:

- `outside-git`: empty directory for the no-output path
- `clean`: tracked branch with no local changes
- `detached-clean`: detached HEAD on a clean commit
- `dirty`: staged, changed, and untracked local work
- `tracking-diverged`: local and remote history diverged after a fetch

The harness reports two layers separately:

- `direct`: invoke the built `glint` binary directly inside each corpus repo
- `shell`: invoke `glint` through a fresh `zsh -f` command-substitution path

That shell measurement is intentionally the current portable fallback, not the
future hook-driven invalidation model. It exists so alpha-era numbers remain
comparable until the first-class shell integration contract is settled.

## Performance Layers

Treat prompt performance as two related but distinct layers.

### Direct Invocation

This is the cost of running `glint` once in a repository.

It covers:

- process startup
- theme/env handling
- Git state collection
- parsing and rendering

This layer should stay small, predictable, and easy to benchmark locally.

### Integrated Shell Usage

This is the cost a user actually feels while typing in a shell prompt setup.

It covers:

- when prompt state is refreshed
- which commands invalidate cached state
- whether directory changes force recomputation
- whether non-Git commands reuse the last known prompt state

The intended first-class contract is now defined in
`docs/spec/shell-integration.md`.

That contract makes three conservative alpha choices explicit:

- the first-class shell surface is `zsh`
- prompt state is invalidated after any real command or directory change
- prompt redraws without an intervening command reuse the cached segment

Direct `$(glint)` substitution remains a useful portable fallback, but it is
not the end-state for a best-in-class prompt component.

## Strategic Direction

The preferred order for performance work is:

1. define a direct invocation budget and measurement method
2. implement the settled shell-integration invalidation contract
3. add regression checks for both layers
4. only then explore a native Git backend if it can beat the porcelain path
   without compromising compatibility

## Guardrails

Prefer these constraints while improving performance:

- keep the compatibility fixture contract authoritative
- keep a simple direct CLI path even if richer shell integration lands later
- do not replace one Git subprocess with many subprocesses in the hot path
- do not add speculative caching without a clear invalidation model
- do not guess that a command was read-only unless that rule becomes an explicit
  part of the contract
- do not claim best-in-class performance from microbenchmarks alone; measure
  both direct invocation and integrated shell behavior
