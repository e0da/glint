# `git_super_status` Contract

## Purpose

This document defines the first alpha compatibility target for `glint`.

## Output Shape

`glint` should emit a single prompt segment shaped like:

```text
(<branch><tracking>|<local status>)
```

## Common-Path Behavior

- Show the current branch name when on a branch.
- Show a detached HEAD hash prefixed with `:`.
- Show ahead/behind counts when tracking a remote.
- Show staged, changed, conflict, and untracked indicators when present.
- Show the clean indicator only when the repository is otherwise clean.
- Produce no output outside a Git repository.

## Prompt Symbols

- Branch marker: `ZSH_THEME_GIT_PROMPT_BRANCH`
- Prefix: `ZSH_THEME_GIT_PROMPT_PREFIX`
- Suffix: `ZSH_THEME_GIT_PROMPT_SUFFIX`
- Separator: `ZSH_THEME_GIT_PROMPT_SEPARATOR`
- Staged: `ZSH_THEME_GIT_PROMPT_STAGED`
- Conflicts: `ZSH_THEME_GIT_PROMPT_CONFLICTS`
- Changed: `ZSH_THEME_GIT_PROMPT_CHANGED`
- Behind: `ZSH_THEME_GIT_PROMPT_BEHIND`
- Ahead: `ZSH_THEME_GIT_PROMPT_AHEAD`
- Untracked: `ZSH_THEME_GIT_PROMPT_UNTRACKED`
- Clean: `ZSH_THEME_GIT_PROMPT_CLEAN`

## In Scope For `0.1.0-alpha.1`

- Clean branch
- Staged only
- Changed only
- Untracked present
- Conflicts plus changed
- Ahead only
- Behind only
- Diverged
- Detached HEAD
- Theme overrides for the core symbols above

## Out Of Scope For The First Alpha

- Caching
- Persistent config files
- Advanced formatting flags
- Full parity for rare upstream edge cases
