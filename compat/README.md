# Compatibility qualification

The oracle is Justin's installed Haskell `gitstatus`, identified by its SHA256,
plus its installed Zsh source and pinned Dots custom prompt. The backend's build
source commit is unknown. The generator does not substitute upstream Python,
clone moving `master`, or install Haskell tooling.

`fixtures/bootstrap-common-path.json` contains ten hand-authored bootstrap
cases. They are useful assertions, not upstream captures.
`fixtures/installed-haskell.generated.json` contains twenty nonempty raw captures:
the same ten Git states with a plain theme and Justin's effective Dots theme.
The file records source/binary hashes, Dots ref/hashes, and Git/Zsh versions.
Normal `cargo test --test compat_fixtures` recreates the Git operations and
compares Glint's raw bytes, including ANSI colors and reset sequences. Only the
bootstrap cases strip reset bytes.

The bounded states are clean, staged, changed, untracked, ahead, behind,
diverged, conflict plus changed, detached with a configured abbreviation, and
theme overrides. This does not establish parity for every Git configuration,
repository size, submodule, unusual filename, unborn branch, or platform.

## Refresh on the qualified host

Retrieve `share/colors.sh` and `share/prompts.zsh` from Dots commit
`d80aeff88a534123dc89d4761e9f086b5d6d5c1f` into temporary input files. The
capturer checks their exact digests and the installed oracle digests before
running any cases. For example, from this checkout:

```bash
cargo build --release
./compat/generate-upstream-fixtures.sh \
  --oracle-root /opt/homebrew/opt/zsh-git-prompt \
  --dots-colors /path/to/pinned/colors.sh \
  --dots-prompt /path/to/pinned/prompts.zsh \
  --candidate target/release/glint \
  --samples 30 \
  --timings /path/to/shell-timings.json
python3 -m unittest discover -s compat -p 'test_*.py'
cargo test --test compat_fixtures
```

The exact installed binary pin is macOS ARM64 specific. A different binary must
be deliberately qualified and reviewed before changing the pin. CI verifies
the captured contract; it does not claim to rerun the installed macOS oracle.

The capture shell uses `zsh -df`, excludes inherited Git/theme/cache variables,
sources defaults before overrides, and forces Haskell. Justin's pinned colors
and prompt are sourced inside a function so interactive `preexec` hooks do not
pollute the captured segment. It compares raw output, Zsh `print -P` rendering,
and the real `e0da_prompt` function with only `git_super_status` substituted by
Glint. Timestamp and host decoration are outside this comparison. No user
startup file or installed prompt is changed.

All inside-Git results must be nonempty. A failed shell, changed digest, empty
capture or candidate mismatch stops refresh before fixture replacement. Output
is replaced atomically only after all cases complete. Timings contain every
sample plus median/p95 for matched shell paths; their scope is the recorded
host and synthetic workloads, not a fleet performance claim.

## Historical capture correction

The March 2026 Ubuntu/Debian comparison produced identical **empty**
`expected_stdout` values. That is evidence of a broken oracle, not compatibility
or a sound base-image choice. The old Dockerfile is retained as historical
scaffolding; the refresh wrapper now invokes the native pinned Haskell path.
The Python generator and existing Git case declarations are retained because
they already express the bounded behavior; the Rust runtime has no Python or
Haskell dependency.

## Public CI admission

The local CI workflow runs only on branch pushes to this repository and manual
dispatch. These require repository write authority. It has no PR-triggered
execution, self-hosted runner label, inherited secrets or write token. It uses a
standard hosted runner, a 15 minute timeout, and preserves the required check
name `rust / Fmt / Clippy / Test / Build` for trusted branch PRs. Outsider PRs do
not get automatic execution; admitting one requires a separate deliberate
policy. Branch protection alone does not prevent fork-triggered execution.

The existing tag-only release workflow still calls shared release tooling with
its own self-hosted/release authority. It is not qualified by source CI. No tag,
release, Homebrew change, installed prompt replacement or dependency removal is
part of this capture qualification. Keep the current Haskell prompt and
rollback path until those gates are separately verified.
