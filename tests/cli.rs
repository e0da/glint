use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::Path;
use std::process::Command;

use tempfile::TempDir;

const RESET: &str = "%{${reset_color}%}";

#[test]
fn outside_git_repo_emits_nothing() {
    let repo = repo();

    assert_output(repo.path(), "");
}

#[test]
fn git_command_failure_emits_nothing() {
    let repo = repo();
    let fake_git = fake_git(
        "\
#!/bin/sh
exit 1
",
    );

    let output = glint(repo.path())
        .env("PATH", fake_git.path())
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let stdout = normalize_output(String::from_utf8(output).unwrap());

    assert_eq!(stdout, "");
}

#[test]
fn incomplete_status_output_emits_nothing() {
    let repo = repo();
    let fake_git = fake_git(
        "\
#!/bin/sh
if [ \"$1\" = \"status\" ]; then
  printf '%s\n' '# branch.oid deadbeef'
  exit 0
fi

exit 1
",
    );

    let output = glint(repo.path())
        .env("PATH", fake_git.path())
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let stdout = normalize_output(String::from_utf8(output).unwrap());

    assert_eq!(stdout, "");
}

#[test]
fn detached_head_without_short_hash_emits_nothing() {
    let repo = repo();
    let fake_git = fake_git(
        "\
#!/bin/sh
if [ \"$1\" = \"status\" ]; then
  printf '%s\n' '# branch.oid 70c2952abcdef012345678901234567890123456'
  printf '%s\n' '# branch.head (detached)'
  exit 0
fi

if [ \"$1\" = \"rev-parse\" ]; then
  exit 1
fi

exit 1
",
    );

    let output = glint(repo.path())
        .env("PATH", fake_git.path())
        .assert()
        .success()
        .get_output()
        .stdout
        .clone();
    let stdout = normalize_output(String::from_utf8(output).unwrap());

    assert_eq!(stdout, "");
}

#[test]
fn clean_branch_renders_expected_output() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");

    assert_output(repo.path(), "(main|✔)");
}

#[test]
fn staged_only_renders_expected_output() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    write_file(repo.path(), "tracked.txt", "updated");
    git(repo.path(), ["add", "tracked.txt"]);

    assert_output(repo.path(), "(main|●1)");
}

#[test]
fn changed_only_renders_expected_output() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    write_file(repo.path(), "tracked.txt", "updated");

    assert_output(repo.path(), "(main|✚1)");
}

#[test]
fn untracked_renders_expected_output() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    write_file(repo.path(), "new.txt", "new");

    assert_output(repo.path(), "(main|…)");
}

#[test]
fn ahead_renders_expected_output() {
    let repo = repo();
    let remote = bare_remote();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    add_remote_and_push(repo.path(), remote.path());
    commit_file(repo.path(), "tracked.txt", "local", "Local commit");

    assert_output(repo.path(), "(main↑1|✔)");
}

#[test]
fn behind_renders_expected_output() {
    let repo = repo();
    let remote = bare_remote();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    add_remote_and_push(repo.path(), remote.path());

    let peer = clone_remote(remote.path());
    commit_file(peer.path(), "peer.txt", "peer", "Peer commit");
    git(peer.path(), ["push", "origin", "main"]);

    git(repo.path(), ["fetch", "origin"]);

    assert_output(repo.path(), "(main↓1|✔)");
}

#[test]
fn diverged_renders_expected_output() {
    let repo = repo();
    let remote = bare_remote();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    add_remote_and_push(repo.path(), remote.path());

    let peer = clone_remote(remote.path());
    commit_file(peer.path(), "peer.txt", "peer", "Peer commit");
    git(peer.path(), ["push", "origin", "main"]);

    commit_file(repo.path(), "local.txt", "local", "Local commit");
    git(repo.path(), ["fetch", "origin"]);

    assert_output(repo.path(), "(main↓1↑1|✔)");
}

#[test]
fn detached_head_respects_git_abbrev_length() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");
    git(repo.path(), ["config", "core.abbrev", "12"]);
    let head = git_output(repo.path(), ["rev-parse", "--short", "HEAD"]);
    git(repo.path(), ["checkout", "--detach"]);

    assert_output(repo.path(), &format!("(:{}|✔)", head.trim()));
}

#[test]
fn theme_overrides_are_honored() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "hello", "Initial commit");

    let mut cmd = glint(repo.path());
    cmd.env("ZSH_THEME_GIT_PROMPT_PREFIX", "[");
    cmd.env("ZSH_THEME_GIT_PROMPT_SUFFIX", "]");
    cmd.env("ZSH_THEME_GIT_PROMPT_SEPARATOR", " :: ");
    cmd.env("ZSH_THEME_GIT_PROMPT_BRANCH", "BR:");
    cmd.env("ZSH_THEME_GIT_PROMPT_CLEAN", "OK");

    let output = cmd.assert().success().get_output().stdout.clone();
    let stdout = normalize_output(String::from_utf8(output).unwrap());

    assert_eq!(stdout, "[BR:main :: OK]");
}

#[test]
fn conflicts_and_changed_render_expected_output() {
    let repo = repo();
    init_repo(repo.path());
    commit_file(repo.path(), "tracked.txt", "base", "Initial commit");

    git(repo.path(), ["checkout", "-b", "feature"]);
    write_file(repo.path(), "tracked.txt", "feature");
    git(repo.path(), ["add", "tracked.txt"]);
    git(repo.path(), ["commit", "-m", "Feature change"]);

    git(repo.path(), ["checkout", "main"]);
    commit_file(repo.path(), "other.txt", "base", "Add second file");

    write_file(repo.path(), "tracked.txt", "main");
    git(repo.path(), ["add", "tracked.txt"]);
    git(repo.path(), ["commit", "-m", "Main change"]);

    let status = Command::new("git")
        .current_dir(repo.path())
        .args(["merge", "feature"])
        .status()
        .expect("merge command should run");
    assert!(!status.success());

    write_file(repo.path(), "other.txt", "changed");

    assert_output(repo.path(), "(main|✖1✚1)");
}

fn assert_output(repo: &Path, expected_plain: &str) {
    let output = glint(repo).assert().success().get_output().stdout.clone();
    let stdout = normalize_output(String::from_utf8(output).unwrap());

    assert_eq!(stdout, expected_plain);
}

fn glint(repo: &Path) -> assert_cmd::Command {
    let mut cmd = assert_cmd::Command::cargo_bin("glint").unwrap();
    cmd.current_dir(repo);
    cmd.env("ZSH_THEME_GIT_PROMPT_PREFIX", "(");
    cmd.env("ZSH_THEME_GIT_PROMPT_SUFFIX", ")");
    cmd.env("ZSH_THEME_GIT_PROMPT_SEPARATOR", "|");
    cmd.env("ZSH_THEME_GIT_PROMPT_BRANCH", "");
    cmd.env("ZSH_THEME_GIT_PROMPT_STAGED", "●");
    cmd.env("ZSH_THEME_GIT_PROMPT_CONFLICTS", "✖");
    cmd.env("ZSH_THEME_GIT_PROMPT_CHANGED", "✚");
    cmd.env("ZSH_THEME_GIT_PROMPT_BEHIND", "↓");
    cmd.env("ZSH_THEME_GIT_PROMPT_AHEAD", "↑");
    cmd.env("ZSH_THEME_GIT_PROMPT_UNTRACKED", "…");
    cmd.env("ZSH_THEME_GIT_PROMPT_CLEAN", "✔");
    cmd
}

fn normalize_output(output: String) -> String {
    output.replace(RESET, "")
}

fn repo() -> TempDir {
    tempfile::tempdir().unwrap()
}

fn bare_remote() -> TempDir {
    let dir = repo();
    git_raw(["init", "--bare", dir.path().to_str().unwrap()]);
    dir
}

fn clone_remote(remote: &Path) -> TempDir {
    let dir = repo();
    git_raw([
        "clone",
        "--branch",
        "main",
        remote.to_str().unwrap(),
        dir.path().to_str().unwrap(),
    ]);
    git(dir.path(), ["config", "user.name", "glint-tests"]);
    git(
        dir.path(),
        ["config", "user.email", "glint-tests@example.com"],
    );
    dir
}

fn init_repo(repo: &Path) {
    git(repo, ["init", "-b", "main"]);
    git(repo, ["config", "user.name", "glint-tests"]);
    git(repo, ["config", "user.email", "glint-tests@example.com"]);
}

fn add_remote_and_push(repo: &Path, remote: &Path) {
    git(repo, ["remote", "add", "origin", remote.to_str().unwrap()]);
    git(repo, ["push", "-u", "origin", "main"]);
}

fn commit_file(repo: &Path, path: &str, contents: &str, message: &str) {
    write_file(repo, path, contents);
    git(repo, ["add", path]);
    git(repo, ["commit", "-m", message]);
}

fn write_file(repo: &Path, path: &str, contents: &str) {
    let full_path = repo.join(path);
    if let Some(parent) = full_path.parent() {
        fs::create_dir_all(parent).unwrap();
    }
    fs::write(full_path, contents).unwrap();
}

fn fake_git(script: &str) -> TempDir {
    let dir = repo();
    let path = dir.path().join("git");
    fs::write(&path, script).unwrap();

    let mut permissions = fs::metadata(&path).unwrap().permissions();
    permissions.set_mode(0o755);
    fs::set_permissions(&path, permissions).unwrap();

    dir
}

fn git(repo: &Path, args: impl IntoIterator<Item = impl AsRef<str>>) {
    let status = Command::new("git")
        .current_dir(repo)
        .args(args.into_iter().map(|arg| arg.as_ref().to_owned()))
        .status()
        .expect("git command should run");

    assert!(status.success());
}

fn git_raw(args: impl IntoIterator<Item = impl AsRef<str>>) {
    let status = Command::new("git")
        .args(args.into_iter().map(|arg| arg.as_ref().to_owned()))
        .status()
        .expect("git command should run");

    assert!(status.success());
}

fn git_output(repo: &Path, args: impl IntoIterator<Item = impl AsRef<str>>) -> String {
    let output = Command::new("git")
        .current_dir(repo)
        .args(args.into_iter().map(|arg| arg.as_ref().to_owned()))
        .output()
        .expect("git command should run");

    assert!(output.status.success());
    String::from_utf8(output.stdout).unwrap()
}
