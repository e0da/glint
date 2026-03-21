#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


UPSTREAM_REPO = os.environ["UPSTREAM_REPO"]
UPSTREAM_REF = os.environ["UPSTREAM_REF"]
UPSTREAM_SCRIPT = os.environ["UPSTREAM_SCRIPT"]
REPO_ROOT = Path("/work")
FIXTURE_PATH = REPO_ROOT / "compat" / "fixtures" / "zsh-git-prompt-common-path.generated.json"

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


def upstream_output(repo: Path, upstream_root: Path, env_overrides=None) -> str:
    script_path = upstream_root / UPSTREAM_SCRIPT
    if not script_path.exists():
        raise RuntimeError(
            f"upstream prompt script not found at {script_path}. "
            "Set UPSTREAM_SCRIPT to the script that defines git_super_status."
        )

    env = os.environ.copy()
    env.update(THEME)
    if env_overrides:
        env.update(env_overrides)
    cmd = [
        "zsh",
        "-lc",
        f"source {script_path} >/dev/null 2>&1 && git_super_status",
    ]
    result = run(cmd, cwd=repo, env=env)
    return result.stdout.rstrip("\n")


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
    upstream_root = Path(tempfile.mkdtemp(prefix="zsh-git-prompt-"))
    run(["git", "clone", UPSTREAM_REPO, str(upstream_root)])
    run(["git", "checkout", UPSTREAM_REF], cwd=upstream_root)

    fixture = {
        "metadata": {
            "source": "zsh-git-prompt",
            "upstream_repo": UPSTREAM_REPO,
            "upstream_ref": UPSTREAM_REF,
            "upstream_script": UPSTREAM_SCRIPT,
            "generator": "compat/capture_upstream.py",
        },
        "cases": build_cases(upstream_root),
    }

    FIXTURE_PATH.write_text(json.dumps(fixture, indent=2) + "\n")


if __name__ == "__main__":
    main()
