# glint

Fast, minimal Git-aware prompt status as a single binary.

`glint` is the planned Rust replacement for `zsh-git-prompt`'s
`git_super_status` prompt segment.

Current state: this repository is in the foundation stage. The binary, crate,
and release artifacts are not in place yet.

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

There is no installable binary yet.

When the Rust crate lands, the local source install path will be:

```bash
cargo install --path .
```

Planned release artifacts will be published from GitHub Releases once the first
alpha is tagged.

---

## Usage

Planned shell integration will replace:

```zsh
$(git_super_status)
```

with:

```zsh
$(glint)
```

That is the target usage, not the current state of the repository.

---

## Compatibility

The first alpha is targeting common-path compatibility with
`zsh-git-prompt`'s `git_super_status`.

The compatibility contract is defined in [docs/spec/git-super-status.md](docs/spec/git-super-status.md).

---

## Docs

- [docs/doctrine.md](docs/doctrine.md)
- [docs/spec/git-super-status.md](docs/spec/git-super-status.md)
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
