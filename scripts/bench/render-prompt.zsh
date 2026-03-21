#!/usr/bin/env zsh
set -eu

binary=${1:?expected glint binary path}

export ZSH_THEME_GIT_PROMPT_PREFIX="("
export ZSH_THEME_GIT_PROMPT_SUFFIX=")"
export ZSH_THEME_GIT_PROMPT_SEPARATOR="|"
export ZSH_THEME_GIT_PROMPT_BRANCH=""
export ZSH_THEME_GIT_PROMPT_STAGED="●"
export ZSH_THEME_GIT_PROMPT_CONFLICTS="✖"
export ZSH_THEME_GIT_PROMPT_CHANGED="✚"
export ZSH_THEME_GIT_PROMPT_BEHIND="↓"
export ZSH_THEME_GIT_PROMPT_AHEAD="↑"
export ZSH_THEME_GIT_PROMPT_UNTRACKED="…"
export ZSH_THEME_GIT_PROMPT_CLEAN="✔"

print -P -- "$("$binary")" >/dev/null
