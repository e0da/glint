#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

UPSTREAM_REPO=${UPSTREAM_REPO:-https://github.com/olivierverdier/zsh-git-prompt.git}
UPSTREAM_REF=${UPSTREAM_REF:-master}
UPSTREAM_SCRIPT=${UPSTREAM_SCRIPT:-gitprompt.sh}
IMAGE_TAG=${IMAGE_TAG:-glint-compat-harness}

docker build -f "$SCRIPT_DIR/Dockerfile" -t "$IMAGE_TAG" "$REPO_ROOT"

docker run --rm \
  -e UPSTREAM_REPO="$UPSTREAM_REPO" \
  -e UPSTREAM_REF="$UPSTREAM_REF" \
  -e UPSTREAM_SCRIPT="$UPSTREAM_SCRIPT" \
  -v "$REPO_ROOT:/work" \
  "$IMAGE_TAG" \
  python3 /work/compat/capture_upstream.py
