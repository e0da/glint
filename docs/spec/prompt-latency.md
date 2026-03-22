# Prompt Latency Contract

## Purpose

This document defines the alpha latency budget for `glint` on the benchmark
corpus carried in this repo.

The benchmark harness exists to keep the performance discussion grounded in
repeatable measurements instead of one-off shell timings.

## Measurement Commands

Use these commands from the repo root:

```sh
./scripts/benchmark.sh direct
./scripts/benchmark.sh shell
./scripts/check-latency.sh
```

`./scripts/benchmark.sh` regenerates the corpus in `tmp/benchmark-corpus/` and
writes raw samples plus a tab-separated summary to `tmp/benchmark-results/`.

## Benchmark Corpus

The alpha corpus consists of these repository shapes:

- `outside-git`
- `clean`
- `detached-clean`
- `dirty`
- `tracking-diverged`

These cases are intentionally small. They cover the direct CLI happy path, the
detached-HEAD extra-Git-call path, and the current no-output fallback outside a
repo.

## Alpha Budget

The alpha budget applies to every corpus repo in the harness summary:

- `direct` median: at most `15 ms`
- `direct` p95: at most `40 ms`
- `shell` median: at most `20 ms`
- `shell` p95: at most `45 ms`

## Shell Assumption

The `shell` mode measures the current portable fallback: a fresh `zsh -f`
invocation that renders prompt output through `$(glint)`.

This is not the hook-driven path described in `docs/spec/shell-integration.md`.
It is only the comparable alpha baseline until that first-class integration is
implemented.

## Guardrails

- Do not compare new numbers against a different corpus and call it equivalent.
- Do not treat multiple smaller Git subprocesses as an acceptable substitute for
  the single porcelain baseline unless the benchmark corpus shows a real win.
- Keep regression checks tied to this harness so the measured budget and the
  enforcement path stay aligned.
