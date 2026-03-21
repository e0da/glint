#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SUMMARY="$ROOT_DIR/tmp/benchmark-results/summary.tsv"

DIRECT_MEDIAN_BUDGET_MS=${GLINT_DIRECT_MEDIAN_BUDGET_MS:-15}
DIRECT_P95_BUDGET_MS=${GLINT_DIRECT_P95_BUDGET_MS:-40}
SHELL_MEDIAN_BUDGET_MS=${GLINT_SHELL_MEDIAN_BUDGET_MS:-20}
SHELL_P95_BUDGET_MS=${GLINT_SHELL_P95_BUDGET_MS:-45}

"$ROOT_DIR/scripts/benchmark.sh" all

awk -F '\t' \
  -v direct_median_budget="$DIRECT_MEDIAN_BUDGET_MS" \
  -v direct_p95_budget="$DIRECT_P95_BUDGET_MS" \
  -v shell_median_budget="$SHELL_MEDIAN_BUDGET_MS" \
  -v shell_p95_budget="$SHELL_P95_BUDGET_MS" '
  NR == 1 {
    next
  }
  {
    mode = $1
    repo = $2
    median = $4 + 0
    p95 = $5 + 0

    median_budget = mode == "direct" ? direct_median_budget : shell_median_budget
    p95_budget = mode == "direct" ? direct_p95_budget : shell_p95_budget

    if (median > median_budget) {
      printf "%s %s median %.3f ms exceeds budget %.3f ms\n", mode, repo, median, median_budget > "/dev/stderr"
      failed = 1
    }

    if (p95 > p95_budget) {
      printf "%s %s p95 %.3f ms exceeds budget %.3f ms\n", mode, repo, p95, p95_budget > "/dev/stderr"
      failed = 1
    }
  }
  END {
    exit failed
  }
' "$SUMMARY"
