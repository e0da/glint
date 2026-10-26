#!/usr/bin/env zsh
# Loading inside a function excludes Dots preexec output from prompt captures.
capture_prompt() {
  root=$1
  profile=$2
  mode=$3
  candidate=$4
  colors_file=$5
  prompt_file=$6
  source "$root/zshrc.sh" || exit
  export GIT_PROMPT_EXECUTABLE=haskell
  unset ZSH_THEME_GIT_PROMPT_CACHE
  if [[ $profile == justin ]]; then
    source "$colors_file" || exit
    DOTS_SHARED=/nonexistent-glint-capture
    source "$prompt_file" || exit
    [[ $__GIT_PROMPT_DIR:A == $root:A ]] || exit 21
  fi
  for key in ${(k)parameters}; do
    if [[ $key == ORACLE_ZSH_THEME_GIT_PROMPT_* ]]; then
      target=${key#ORACLE_}
      typeset -gx "$target=${(P)key}"
    fi
  done
  if [[ $mode == theme ]]; then
    for key in ${(ok)parameters}; do
      if [[ $key == ZSH_THEME_GIT_PROMPT_* ]]; then
        print -rN -- "$key" "${(P)key}"
      fi
    done
    exit 0
  fi
  if [[ $candidate != oracle ]]; then
    git_super_status() { "$candidate"; }
  fi
  case $mode in
    raw) segment=$(git_super_status) || return
         print -rn -- "$segment" ;;
    rendered) segment=$(git_super_status) || return
              print -Prn -- "$segment" ;;
    dots) print -Prn -- "$(e0da_prompt)" ;;
    *) exit 22 ;;
  esac

}
capture_prompt "$@"
