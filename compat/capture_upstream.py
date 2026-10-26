#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import statistics
import time
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "compat/fixtures/installed-haskell.generated.json"
PINS = {
    "zshrc.sh": "8a150a198354c9fd4da15d626b64e526fe42038608b5fb2bf564ac590ca1c6c4",
    "src/.bin/gitstatus": "a9f9b5f903a05764320c8cad5ec73e7514e3f9ffff530c9793cd89233cad144d",
}
DOTS_PINS = {
    "colors": "e00e2f7aa9641ed7e7a4f8a1d107591f3b6707e9561b5c1e3c4885b482fa1e8a",
    "prompt": "70021910bb9ec5503ac1f69b22ed2c32676677f4e153358ebb9a7b29f0d6daf0",
}
PROFILE = "plain"
COLORS = ""
PROMPT = ""
CANDIDATE = None
SAMPLES = 0
MEASUREMENTS = []

THEME = {
    "ZSH_THEME_GIT_PROMPT_PREFIX": "(",
    "ZSH_THEME_GIT_PROMPT_SUFFIX": ")",
    "ZSH_THEME_GIT_PROMPT_SEPARATOR": "|",
    "ZSH_THEME_GIT_PROMPT_BRANCH": "",
    "ZSH_THEME_GIT_PROMPT_STAGED": "●",
    "ZSH_THEME_GIT_PROMPT_CONFLICTS": "✖",
    "ZSH_THEME_GIT_PROMPT_CHANGED": "✚",
    "ZSH_THEME_GIT_PROMPT_BEHIND": "↓",
    "ZSH_THEME_GIT_PROMPT_AHEAD": "↑",
    "ZSH_THEME_GIT_PROMPT_UNTRACKED": "…",
    "ZSH_THEME_GIT_PROMPT_CLEAN": "✔",
}


@dataclass
class Context:
    root: Path

    def repo(self, name: str) -> Path:
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        return path


def run(cmd, cwd=None, env=None, check=True):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed: {cmd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def git(repo: Path, *args: str, check=True):
    return run(["git", *args], cwd=repo, check=check)


def write_file(repo: Path, relative_path: str, contents: str):
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)


def init_repo(repo: Path):
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "glint-compat")
    git(repo, "config", "user.email", "glint-compat@example.com")


def commit_file(repo: Path, relative_path: str, contents: str, message: str):
    write_file(repo, relative_path, contents)
    git(repo, "add", relative_path)
    git(repo, "commit", "-m", message)


def add_remote_and_push(repo: Path, remote: Path):
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")


def clone_remote(remote: Path, repo: Path):
    shutil.rmtree(repo)
    run(["git", "clone", "--branch", "main", str(remote), str(repo)])
    git(repo, "config", "user.name", "glint-compat")
    git(repo, "config", "user.email", "glint-compat@example.com")


def require_prompt(output):
    if not output.strip():
        raise RuntimeError("empty inside-Git oracle output")
    return output


def verify_digest(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"oracle digest mismatch: {path}: {actual}")


def shell_output(repo, root, mode, candidate="oracle", overrides=None):
    # Keep Git configuration, startup files and inherited theme/cache variables out.
    env = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR") if key in os.environ}
    env.update(TERM="xterm-256color", LC_ALL="C.UTF-8", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_NOSYSTEM="1")
    theme = dict(THEME) if PROFILE == "plain" else {}
    theme.update(overrides or {})
    env.update({"ORACLE_" + key: value for key, value in theme.items()})
    return run(["zsh", "-df", str(REPO_ROOT / "compat/oracle.zsh"), str(root),
                PROFILE, mode, str(candidate), str(COLORS), str(PROMPT)], cwd=repo, env=env).stdout


def effective_theme(repo, root, overrides=None):
    fields = shell_output(repo, root, "theme", overrides=overrides).split("\0")
    if fields[-1] == "":
        fields.pop()
    return dict(zip(fields[::2], fields[1::2], strict=True))


def upstream_output(repo: Path, upstream_root: Path, env_overrides=None) -> str:
    output = require_prompt(shell_output(repo, upstream_root, "raw", overrides=env_overrides))
    if CANDIDATE:
        modes = ["raw", "rendered"] + (["dots"] if PROFILE == "justin" else [])
        for mode in modes:
            expected = shell_output(repo, upstream_root, mode, overrides=env_overrides)
            actual = shell_output(repo, upstream_root, mode, CANDIDATE, env_overrides)
            if actual != expected:
                raise RuntimeError(f"{PROFILE}/{repo.parent.name}/{mode} mismatch\n"
                                   f"oracle={expected!r}\nglint ={actual!r}")
        mode = "dots" if PROFILE == "justin" else "rendered"
        timings = {"oracle": [], "glint": []}
        for _ in range(SAMPLES):
            for name, binary in (("oracle", "oracle"), ("glint", CANDIDATE)):
                started = time.perf_counter_ns()
                shell_output(repo, upstream_root, mode, binary, env_overrides)
                timings[name].append((time.perf_counter_ns() - started) / 1_000_000)
        if SAMPLES:
            MEASUREMENTS.append({"profile": PROFILE, "case": repo.parent.name,
                                 "mode": mode, "samples_ms": timings})
    return output


def git_output(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.strip()


def build_cases(upstream_root: Path):
    cases = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)

        def case_context(name: str) -> Context:
            root = tmp_root / name
            root.mkdir(parents=True, exist_ok=True)
            return Context(root)

        def seeded_repo(ctx: Context) -> Path:
            repo = ctx.repo("repo")
            init_repo(repo)
            commit_file(repo, "tracked.txt", "hello", "Initial commit")
            return repo

        ctx = case_context("clean_branch")
        repo = seeded_repo(ctx)
        cases.append(
            {
                "name": "clean_branch",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                ],
            }
        )

        ctx = case_context("staged_only")
        repo = seeded_repo(ctx)
        write_file(repo, "tracked.txt", "updated")
        git(repo, "add", "tracked.txt")
        cases.append(
            {
                "name": "staged_only",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "write_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "updated",
                    },
                    {"type": "git", "repo": "repo", "args": ["add", "tracked.txt"]},
                ],
            }
        )

        ctx = case_context("changed_only")
        repo = seeded_repo(ctx)
        write_file(repo, "tracked.txt", "updated")
        cases.append(
            {
                "name": "changed_only",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "write_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "updated",
                    },
                ],
            }
        )

        ctx = case_context("untracked")
        repo = seeded_repo(ctx)
        write_file(repo, "new.txt", "new")
        cases.append(
            {
                "name": "untracked",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "write_file",
                        "repo": "repo",
                        "path": "new.txt",
                        "contents": "new",
                    },
                ],
            }
        )

        ctx = case_context("ahead_only")
        repo = seeded_repo(ctx)
        origin = ctx.repo("origin")
        git(origin, "init", "--bare")
        add_remote_and_push(repo, origin)
        commit_file(repo, "tracked.txt", "local", "Local commit")
        cases.append(
            {
                "name": "ahead_only",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "bare_remote", "repo": "origin"},
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "add_remote_and_push",
                        "repo": "repo",
                        "remote": "origin",
                    },
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "local",
                        "message": "Local commit",
                    },
                ],
            }
        )

        ctx = case_context("behind_only")
        repo = seeded_repo(ctx)
        origin = ctx.repo("origin")
        peer = ctx.repo("peer")
        git(origin, "init", "--bare")
        add_remote_and_push(repo, origin)
        clone_remote(origin, peer)
        commit_file(peer, "peer.txt", "peer", "Peer commit")
        git(peer, "push", "origin", "main")
        git(repo, "fetch", "origin")
        cases.append(
            {
                "name": "behind_only",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "bare_remote", "repo": "origin"},
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "add_remote_and_push",
                        "repo": "repo",
                        "remote": "origin",
                    },
                    {
                        "type": "clone_remote",
                        "repo": "peer",
                        "remote": "origin",
                    },
                    {
                        "type": "commit_file",
                        "repo": "peer",
                        "path": "peer.txt",
                        "contents": "peer",
                        "message": "Peer commit",
                    },
                    {"type": "git", "repo": "peer", "args": ["push", "origin", "main"]},
                    {"type": "git", "repo": "repo", "args": ["fetch", "origin"]},
                ],
            }
        )

        ctx = case_context("diverged")
        repo = seeded_repo(ctx)
        origin = ctx.repo("origin")
        peer = ctx.repo("peer")
        git(origin, "init", "--bare")
        add_remote_and_push(repo, origin)
        clone_remote(origin, peer)
        commit_file(peer, "peer.txt", "peer", "Peer commit")
        git(peer, "push", "origin", "main")
        commit_file(repo, "local.txt", "local", "Local commit")
        git(repo, "fetch", "origin")
        cases.append(
            {
                "name": "diverged",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "bare_remote", "repo": "origin"},
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "add_remote_and_push",
                        "repo": "repo",
                        "remote": "origin",
                    },
                    {
                        "type": "clone_remote",
                        "repo": "peer",
                        "remote": "origin",
                    },
                    {
                        "type": "commit_file",
                        "repo": "peer",
                        "path": "peer.txt",
                        "contents": "peer",
                        "message": "Peer commit",
                    },
                    {"type": "git", "repo": "peer", "args": ["push", "origin", "main"]},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "local.txt",
                        "contents": "local",
                        "message": "Local commit",
                    },
                    {"type": "git", "repo": "repo", "args": ["fetch", "origin"]},
                ],
            }
        )

        ctx = case_context("conflicts_and_changed")
        repo = seeded_repo(ctx)
        git(repo, "checkout", "-b", "feature")
        write_file(repo, "tracked.txt", "feature")
        git(repo, "add", "tracked.txt")
        git(repo, "commit", "-m", "Feature change")
        git(repo, "checkout", "main")
        commit_file(repo, "other.txt", "base", "Add second file")
        write_file(repo, "tracked.txt", "main")
        git(repo, "add", "tracked.txt")
        git(repo, "commit", "-m", "Main change")
        merge_result = git(repo, "merge", "feature", check=False)
        if merge_result.returncode == 0:
            raise RuntimeError("expected merge conflict when capturing conflicts_and_changed")
        write_file(repo, "other.txt", "changed")
        cases.append(
            {
                "name": "conflicts_and_changed",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {"type": "git", "repo": "repo", "args": ["checkout", "-b", "feature"]},
                    {
                        "type": "write_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "feature",
                    },
                    {"type": "git", "repo": "repo", "args": ["add", "tracked.txt"]},
                    {
                        "type": "git",
                        "repo": "repo",
                        "args": ["commit", "-m", "Feature change"],
                    },
                    {"type": "git", "repo": "repo", "args": ["checkout", "main"]},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "other.txt",
                        "contents": "base",
                        "message": "Add second file",
                    },
                    {
                        "type": "write_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "main",
                    },
                    {"type": "git", "repo": "repo", "args": ["add", "tracked.txt"]},
                    {
                        "type": "git",
                        "repo": "repo",
                        "args": ["commit", "-m", "Main change"],
                    },
                    {
                        "type": "git",
                        "repo": "repo",
                        "args": ["merge", "feature"],
                        "expect_success": False,
                    },
                    {
                        "type": "write_file",
                        "repo": "repo",
                        "path": "other.txt",
                        "contents": "changed",
                    },
                ],
            }
        )

        ctx = case_context("detached_head_abbrev")
        repo = seeded_repo(ctx)
        git(repo, "config", "core.abbrev", "12")
        git(repo, "checkout", "--detach")
        short_head = git_output(repo, "rev-parse", "--short", "HEAD")
        expected_stdout = upstream_output(repo, upstream_root).replace(
            f":{short_head}",
            ":{{git_short_head:repo}}",
            1,
        )
        cases.append(
            {
                "name": "detached_head_abbrev",
                "expected_stdout": expected_stdout,
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "git",
                        "repo": "repo",
                        "args": ["config", "core.abbrev", "12"],
                    },
                    {"type": "git", "repo": "repo", "args": ["checkout", "--detach"]},
                ],
            }
        )

        ctx = case_context("theme_overrides")
        repo = seeded_repo(ctx)
        env = {
            "ZSH_THEME_GIT_PROMPT_PREFIX": "[",
            "ZSH_THEME_GIT_PROMPT_SUFFIX": "]",
            "ZSH_THEME_GIT_PROMPT_SEPARATOR": " :: ",
            "ZSH_THEME_GIT_PROMPT_BRANCH": "BR:",
            "ZSH_THEME_GIT_PROMPT_CLEAN": "OK",
        }
        cases.append(
            {
                "name": "theme_overrides",
                "expected_stdout": upstream_output(repo, upstream_root, env),
                "env": env,
                "operations": [
                    {"type": "init_repo", "repo": "repo"},
                    {
                        "type": "commit_file",
                        "repo": "repo",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                ],
            }
        )

    return cases


def main():
    global PROFILE, COLORS, PROMPT, CANDIDATE, SAMPLES
    parser = argparse.ArgumentParser(description="Capture the digest-pinned installed Haskell oracle")
    parser.add_argument("--oracle-root", type=Path, required=True)
    parser.add_argument("--dots-colors", type=Path, required=True)
    parser.add_argument("--dots-prompt", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--samples", type=int, default=0)
    parser.add_argument("--output", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--timings", type=Path)
    args = parser.parse_args()
    if args.samples < 0 or (args.samples and (not args.candidate or not args.timings)):
        parser.error("samples require candidate and timings, and must be nonnegative")
    for relative, digest in PINS.items():
        verify_digest(args.oracle_root / relative, digest)
    verify_digest(args.dots_colors, DOTS_PINS["colors"])
    verify_digest(args.dots_prompt, DOTS_PINS["prompt"])
    COLORS, PROMPT = args.dots_colors.resolve(), args.dots_prompt.resolve()
    CANDIDATE = args.candidate.resolve() if args.candidate else None
    SAMPLES = args.samples
    cases = []
    for PROFILE in ("plain", "justin"):
        captured = build_cases(args.oracle_root)
        for case in captured:
            case["env"] = effective_theme(REPO_ROOT, args.oracle_root, case.get("env"))
            case["name"] = PROFILE + "/" + case["name"]
            cases.append(case)
    fixture = {
        "metadata": {
            "oracle": "installed Haskell binary; build source commit unknown",
            "sha256": PINS,
            "shell_source": "olivierverdier/zsh-git-prompt@0a6c8b610e799040b612db8888945f502a2ddd9d (trailing blank lines differ)",
            "dots_ref": "d80aeff88a534123dc89d4761e9f086b5d6d5c1f",
            "dots_sha256": DOTS_PINS,
            "generator": "compat/capture_upstream.py",
            "git_version": run(["git", "--version"]).stdout.strip(),
            "zsh_version": run(["zsh", "--version"]).stdout.strip(),
        },
        "raw": True,
        "cases": cases,
    }
    # No partial or empty result may replace an accepted capture.
    for case in cases:
        require_prompt(case["expected_stdout"])
    write_json(args.output, fixture)
    if args.timings:
        summaries = []
        for measurement in MEASUREMENTS:
            summary = {key: value for key, value in measurement.items() if key != "samples_ms"}
            for name, samples in measurement["samples_ms"].items():
                summary[name] = {"median_ms": statistics.median(samples),
                                 "p95_ms": sorted(samples)[math.ceil(len(samples) * .95) - 1]}
            summaries.append(summary)
        write_json(args.timings, {"measurements": MEASUREMENTS, "summary": summaries})
    print(f"Captured {len(cases)} nonempty pinned Haskell cases into {args.output}")


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


if __name__ == "__main__":
    main()
