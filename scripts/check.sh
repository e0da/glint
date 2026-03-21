#!/bin/sh
set -eu

if [ ! -f Cargo.toml ]; then
  echo "No Cargo.toml yet; skipping Rust checks on the bootstrap branch."
  exit 0
fi

cargo fmt --all --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
cargo build --release
./scripts/check-latency.sh
