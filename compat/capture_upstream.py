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


def upstream_output(repo: Path, upstream_root: Path) -> str:
    script_path = upstream_root / UPSTREAM_SCRIPT
    if not script_path.exists():
        raise RuntimeError(
            f"upstream prompt script not found at {script_path}. "
            "Set UPSTREAM_SCRIPT to the script that defines git_super_status."
        )

    env = os.environ.copy()
    env.update(THEME)
    cmd = [
        "zsh",
        "-lc",
        f"source {script_path} >/dev/null 2>&1 && git_super_status",
    ]
    result = run(cmd, cwd=repo, env=env)
    return result.stdout.strip()


def build_cases(upstream_root: Path):
    cases = []

    with tempfile.TemporaryDirectory() as tmp:
        ctx = Context(Path(tmp))

        repo = ctx.repo("repo")
        init_repo(repo)
        commit_file(repo, "tracked.txt", "hello", "Initial commit")
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

        repo = ctx.repo("changed")
        init_repo(repo)
        commit_file(repo, "tracked.txt", "hello", "Initial commit")
        write_file(repo, "tracked.txt", "updated")
        cases.append(
            {
                "name": "changed_only",
                "target_repo": "changed",
                "expected_stdout": upstream_output(repo, upstream_root),
                "operations": [
                    {"type": "init_repo", "repo": "changed"},
                    {
                        "type": "commit_file",
                        "repo": "changed",
                        "path": "tracked.txt",
                        "contents": "hello",
                        "message": "Initial commit",
                    },
                    {
                        "type": "write_file",
                        "repo": "changed",
                        "path": "tracked.txt",
                        "contents": "updated",
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
