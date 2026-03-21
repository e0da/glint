#!/usr/bin/env zsh
set -eu

zmodload zsh/datetime

runs=${1:?expected run count}
warmup=${2:?expected warmup count}
cwd=${3:?expected cwd}
shift 3

cd "$cwd"

integer i
for ((i = 0; i < warmup; i += 1)); do
  "$@" >/dev/null
done

for ((i = 0; i < runs; i += 1)); do
  start=$EPOCHREALTIME
  "$@" >/dev/null
  end=$EPOCHREALTIME
  printf '%.6f\n' "$(((end - start) * 1000.0))"
done
