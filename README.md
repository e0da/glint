# glint

Fast, minimal Git-aware prompt status as a single binary.

`glint` is the Rust replacement for `zsh-git-prompt`'s
`git_super_status` prompt segment.

Current state: the foundation-stage crate and binary are in place. Local source
installs work today; GitHub Release artifacts remain alpha-stage follow-up
work.

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

Local source install is available now:

```bash
cargo install --path .
```

GitHub Release artifacts are planned once the first alpha is tagged.

---

## Usage

Shell integration target:

```zsh
$(git_super_status)
```

with:

```zsh
$(glint)
```

The contract and output coverage are still being tightened as the alpha stack
lands, but the binary already emits the prompt segment shape described here.

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
