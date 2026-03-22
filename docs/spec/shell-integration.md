# Shell Integration Contract

## Purpose

This document defines the first-class shell integration target for `glint`
after the direct `$(glint)` fallback.

It is a contract for the intended high-performance path, not a claim that the
hook-driven path is already implemented.

## Alpha Scope

The first-class shell integration target for `0.1.0-alpha.1` is:

- `zsh` only
- hook-driven invalidation with no background daemon
- the same visible prompt output contract as direct `glint` execution

Other shells, or `zsh` setups where the required hooks are unavailable, should
fall back to direct `$(glint)` execution.

## Hook Surface

The supported hook surface is:

- `precmd` to render or reuse the prompt segment before the prompt is shown
- `preexec` to mark cached prompt state dirty before a real command runs
- `chpwd` to invalidate cached prompt state when the working directory changes

This keeps the integration explicit and shell-native instead of inventing a
hidden service layer.

## Invalidation Model

The first-class path should cache only the last rendered segment for the
current shell session.

Recompute the prompt segment when any of these are true:

- no cached segment exists yet
- the previous command triggered `preexec`
- the shell triggered `chpwd`
- the current working directory differs from the directory used for the cached
  segment

Reuse the cached segment when the prompt redraws without an intervening command
or directory change.

## Command Classes

For the alpha contract, treat commands conservatively:

- any real command execution invalidates the cached prompt state
- prompt redraws with no intervening command reuse the cached prompt state
- directory changes always invalidate the cached prompt state

The alpha contract does not attempt a read-only command allowlist. If a command
ran, `glint` should recompute before the next prompt rather than guessing
whether the repo stayed unchanged.

## Fallback Behavior

The portable fallback remains direct command substitution:

```zsh
$(glint)
```

Fallback mode should:

- remain the only supported path outside the first-class `zsh` hook surface
- preserve the same visible output contract as the hook-driven path
- avoid hidden caches, daemons, or partial emulation of hook behavior

## Benchmark And Test Assumptions

Until the hook-driven path exists, the benchmark harness should keep measuring
the direct substitution fallback for the `shell` layer.

When the hook-driven path is implemented, test and benchmark it against at
least these cases:

- repeated prompt redraw with no intervening command reuses cached output
- a completed command invalidates prompt state before the next prompt
- a directory change invalidates prompt state before the next prompt
