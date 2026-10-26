# glint

Fast, minimal Git-aware prompt status as a single binary.

`glint` is the Rust replacement for `zsh-git-prompt`'s
`git_super_status` prompt segment.

Current state: the crate and CLI are in place, direct source installs work, and
the first alpha contract is still being finished. Tagged release artifacts and
hook-driven shell integration are not shipped yet.

---

## Why

`zsh-git-prompt` is useful, but it brings shell-heavy logic and extra runtime
surface area.

`glint` is intended to keep the same common-path behavior in a small Rust
binary:

- no prompt scripting dependency
- one executable
- planned GitHub Release artifacts once the first alpha tag exists

The first shipped version target is `0.1.0-alpha.1`.

---

## Scope

- Git prompt status for the common path
- Common-path alpha compatibility with `zsh-git-prompt`'s `git_super_status`
- Executable compatibility fixtures and integration tests for user-visible output

---

## Install

Source installs work today:

```bash
cargo install --path .
```

Tagged release artifacts are not published yet. Those will land through GitHub
Releases once the first alpha is tagged.

---

## Usage

`glint --version` (or `-V`) prints the Cargo package name and version without
Git access. `glint --help` (or `-h`) prints usage. Unsupported or surplus arguments
exit with status 2 and usage on stderr. With no arguments, prompt-safe behavior
is unchanged.

Current portable usage is direct command substitution:

```zsh
$(glint)
```

That path works today from a source install. It is the current fallback path,
not the long-term high-performance integration.

The planned higher-performance shell integration is defined in
[docs/spec/shell-integration.md](docs/spec/shell-integration.md), but that
hook-driven path is not shipped yet.

---

## Compatibility

The first alpha is targeting common-path compatibility with
`zsh-git-prompt`'s `git_super_status`.

The compatibility contract is defined in [docs/spec/git-super-status.md](docs/spec/git-super-status.md).
Current automated coverage includes twenty raw captures from the digest-pinned
installed Haskell backend, with plain and pinned Dots themes. The capture harness
also compares actual Zsh rendering and the Dots `e0da_prompt` function. See
[compat/README.md](compat/README.md) for provenance, refresh commands, CI admission
and qualification limits. Installed prompt replacement and tagged releases remain
separate gates.

---

## Docs

- [docs/doctrine.md](docs/doctrine.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/spec/git-super-status.md](docs/spec/git-super-status.md)
- [docs/spec/prompt-latency.md](docs/spec/prompt-latency.md)
- [docs/spec/shell-integration.md](docs/spec/shell-integration.md)
- [CHANGELOG.md](CHANGELOG.md)

---

## Non-Goals

- Becoming a full prompt framework
- Replacing tools like Starship or Powerlevel10k
- Exposing a large configuration surface in the first alpha

---

## Inspiration

Inspired by [zsh-git-prompt](https://github.com/olivierverdier/zsh-git-prompt).
The implementation target is Rust.

---

## License

MIT
