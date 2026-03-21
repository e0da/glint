#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
CORPUS_DIR=${GLINT_BENCH_CORPUS_DIR:-"$ROOT_DIR/tmp/benchmark-corpus"}
RESULTS_DIR=${GLINT_BENCH_RESULTS_DIR:-"$ROOT_DIR/tmp/benchmark-results"}
RUNS=${GLINT_BENCH_RUNS:-30}
WARMUP=${GLINT_BENCH_WARMUP:-5}
MODE=${1:-all}

case "$MODE" in
  direct|shell|all)
    ;;
  *)
    echo "usage: $0 [direct|shell|all]" >&2
    exit 1
    ;;
esac

mkdir -p "$RESULTS_DIR"
rm -f "$RESULTS_DIR"/*.samples.txt "$RESULTS_DIR"/summary.tsv

"$ROOT_DIR/scripts/bench/prepare-corpus.sh" "$CORPUS_DIR" >/dev/null
cargo build --release >/dev/null

BINARY="$ROOT_DIR/target/release/glint"
RUNNER="$ROOT_DIR/scripts/bench/run-timed.zsh"
SHELL_RENDER="$ROOT_DIR/scripts/bench/render-prompt.zsh"
SUMMARY="$RESULTS_DIR/summary.tsv"

printf 'mode\trepo\truns\tmedian_ms\tp95_ms\tmean_ms\tmin_ms\tmax_ms\n' > "$SUMMARY"

summarize_case() {
  mode=$1
  repo_name=$2
  cwd=$3
  shift 3

  sample_file="$RESULTS_DIR/$mode-$repo_name.samples.txt"
  "$RUNNER" "$RUNS" "$WARMUP" "$cwd" "$@" > "$sample_file"

  sort -n "$sample_file" | awk -v mode="$mode" -v repo="$repo_name" -v runs="$RUNS" '
    {
      values[NR] = $1
      sum += $1
    }
    END {
      if (NR == 0) {
        exit 1
      }

      min = values[1]
      max = values[NR]
      mean = sum / NR
      p95_index = int((NR * 95 + 99) / 100)
      if (p95_index < 1) {
        p95_index = 1
      }
      if (p95_index > NR) {
        p95_index = NR
      }

      if (NR % 2 == 1) {
        median = values[(NR + 1) / 2]
      } else {
        median = (values[NR / 2] + values[(NR / 2) + 1]) / 2
      }

      printf "%s\t%s\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\n",
        mode,
        repo,
        runs,
        median,
        values[p95_index],
        mean,
        min,
        max
    }
  ' >> "$SUMMARY"
}

run_direct() {
  repo_name=$1
  cwd=$2
  summarize_case direct "$repo_name" "$cwd" "$BINARY"
}

run_shell() {
  repo_name=$1
  cwd=$2
  summarize_case shell "$repo_name" "$cwd" zsh -f "$SHELL_RENDER" "$BINARY"
}

for repo_name in outside-git clean detached-clean dirty tracking-diverged; do
  repo_path="$CORPUS_DIR/$repo_name"

  if [ "$MODE" = "direct" ] || [ "$MODE" = "all" ]; then
    run_direct "$repo_name" "$repo_path"
  fi

  if [ "$MODE" = "shell" ] || [ "$MODE" = "all" ]; then
    run_shell "$repo_name" "$repo_path"
  fi
done

awk '
  BEGIN {
    printf "%-8s %-18s %6s %10s %10s %10s %10s %10s\n",
      "mode",
      "repo",
      "runs",
      "median_ms",
      "p95_ms",
      "mean_ms",
      "min_ms",
      "max_ms"
  }
  NR == 1 {
    next
  }
  {
    printf "%-8s %-18s %6s %10s %10s %10s %10s %10s\n",
      $1,
      $2,
      $3,
      $4,
      $5,
      $6,
      $7,
      $8
  }
' "$SUMMARY"

printf '\nSaved raw samples and summary under %s\n' "$RESULTS_DIR"
