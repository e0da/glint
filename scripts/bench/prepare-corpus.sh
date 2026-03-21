#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
OUT_DIR=${1:-"$ROOT_DIR/tmp/benchmark-corpus"}

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

git_init_repo() {
  repo=$1
  git init -b main "$repo" >/dev/null
  git -C "$repo" config user.name glint-bench >/dev/null
  git -C "$repo" config user.email glint-bench@example.com >/dev/null
}

write_file() {
  path=$1
  contents=$2
  mkdir -p "$(dirname "$path")"
  printf '%s\n' "$contents" > "$path"
}

commit_file() {
  repo=$1
  path=$2
  contents=$3
  message=$4
  write_file "$repo/$path" "$contents"
  git -C "$repo" add "$path"
  git -C "$repo" commit -m "$message" >/dev/null
}

outside_git_repo() {
  mkdir -p "$OUT_DIR/outside-git"
}

clean_repo() {
  repo="$OUT_DIR/clean"
  git_init_repo "$repo"
  commit_file "$repo" tracked.txt "clean" "Initial commit"
}

detached_clean_repo() {
  repo="$OUT_DIR/detached-clean"
  git_init_repo "$repo"
  commit_file "$repo" tracked.txt "detached" "Initial commit"
  git -C "$repo" checkout --detach >/dev/null 2>&1
}

dirty_repo() {
  repo="$OUT_DIR/dirty"
  git_init_repo "$repo"
  commit_file "$repo" tracked.txt "clean" "Initial commit"
  commit_file "$repo" changed.txt "base" "Add changed file"
  write_file "$repo/staged.txt" "staged"
  git -C "$repo" add staged.txt
  write_file "$repo/changed.txt" "dirty"
  write_file "$repo/untracked.txt" "untracked"
}

tracking_diverged_repo() {
  remote="$OUT_DIR/tracking-diverged-remote.git"
  repo="$OUT_DIR/tracking-diverged"
  peer="$OUT_DIR/tracking-diverged-peer"

  git init --bare "$remote" >/dev/null
  git_init_repo "$repo"
  commit_file "$repo" tracked.txt "base" "Initial commit"
  git -C "$repo" remote add origin "$remote"
  git -C "$repo" push -u origin main >/dev/null

  git clone --branch main "$remote" "$peer" >/dev/null
  git -C "$peer" config user.name glint-bench >/dev/null
  git -C "$peer" config user.email glint-bench@example.com >/dev/null
  commit_file "$peer" peer.txt "peer" "Peer commit"
  git -C "$peer" push origin main >/dev/null

  commit_file "$repo" local.txt "local" "Local commit"
  git -C "$repo" fetch origin >/dev/null

  rm -rf "$peer"
}

outside_git_repo
clean_repo
detached_clean_repo
dirty_repo
tracking_diverged_repo

printf '%s\n' \
  "$OUT_DIR/outside-git" \
  "$OUT_DIR/clean" \
  "$OUT_DIR/detached-clean" \
  "$OUT_DIR/dirty" \
  "$OUT_DIR/tracking-diverged"
