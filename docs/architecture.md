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

Upstream `zsh-git-prompt` already wins some real-world latency here through hook
driven invalidation. A direct `$(glint)` substitution remains a useful fallback,
but it is not the end-state for a best-in-class prompt component.

## Strategic Direction

The preferred order for performance work is:

1. define a direct invocation budget and measurement method
2. define a shell-integration invalidation strategy that avoids needless runs
3. add regression checks for both layers
4. only then explore a native Git backend if it can beat the porcelain path
   without compromising compatibility

## Guardrails

Prefer these constraints while improving performance:

- keep the compatibility fixture contract authoritative
- keep a simple direct CLI path even if richer shell integration lands later
- do not replace one Git subprocess with many subprocesses in the hot path
- do not add speculative caching without a clear invalidation model
- do not claim best-in-class performance from microbenchmarks alone; measure
  both direct invocation and integrated shell behavior
