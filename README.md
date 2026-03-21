# glint

Fast, minimal Git-aware prompt status as a single binary.

`glint` is the Rust replacement for `zsh-git-prompt`'s
`git_super_status` prompt segment.

Current state: the crate and CLI are in place, source installs work, and the
compatibility surface is still being built out for the first alpha.

---

## Why

`zsh-git-prompt` is useful, but it brings shell-heavy logic and extra runtime
surface area.

`glint` is intended to keep the same common-path behavior in a small Rust
binary:

- no prompt scripting dependency
- one executable
- releaseable through GitHub Releases

The first shipped version target is `0.1.0-alpha.1`.

---

## Scope

- Git prompt status for the common path
- Compatibility with `zsh-git-prompt`'s `git_super_status`
- Trunk-based development with Graphite stacks
- Executable specs and golden tests for user-visible output

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

The intended shell integration is:

```zsh
$(git_super_status)
```

with:

```zsh
$(glint)
```

That command already runs locally from the crate in this repo. The remaining
work is narrowing the output toward the compatibility contract.

Direct command substitution is the current portable fallback. A higher
performance shell integration will likely use hook-driven invalidation so
`glint` does not need to recompute on every prompt render.

---

## Compatibility

The first alpha is targeting common-path compatibility with
`zsh-git-prompt`'s `git_super_status`.

The compatibility contract is defined in [docs/spec/git-super-status.md](docs/spec/git-super-status.md).

---

## Docs

- [docs/doctrine.md](docs/doctrine.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/spec/git-super-status.md](docs/spec/git-super-status.md)
- [docs/spec/prompt-latency.md](docs/spec/prompt-latency.md)
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
