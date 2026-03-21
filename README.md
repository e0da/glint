# glint

Fast, minimal Git-aware prompt status as a single binary.

A drop-in replacement for `zsh-git-prompt`—without the runtime baggage.

---

## Why

`zsh-git-prompt` is great, but it often pulls in extra dependencies (e.g. Haskell/GHC builds or shell-heavy logic).

glint takes the same idea and compiles it into a small, fast binary:

- no runtime dependencies
- no shell gymnastics
- just one executable

---

## Features

- Git status for your shell prompt
- Designed to be a drop-in replacement
- Fast execution (built in Rust)
- Single static binary distribution
- Minimal configuration

---

## Install

### From source

```bash
cargo install --path .
```

### From release (planned)

Download a prebuilt binary from GitHub Releases.

---

## Usage

Replace your existing prompt call:

```zsh
$(git_super_status)
```

with:

```zsh
$(glint)
```

That’s it.

---

## Compatibility

glint aims to be compatible with the output and behavior of
`zsh-git-prompt`’s `git_super_status`.

Not all features are guaranteed initially—focus is on the common path first.

---

## Design Goals

- Be fast enough to run on every prompt render
- Avoid external dependencies
- Keep the implementation simple and auditable
- Match existing workflows instead of inventing new ones

---

## Non-Goals

- Becoming a full prompt framework
- Replacing tools like Starship or Powerlevel10k
- Over-configurability

---

## Inspiration

Inspired by:

- https://github.com/olivierverdier/zsh-git-prompt

Reimplemented in Rust as a standalone binary.

---

## License

MIT
