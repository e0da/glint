use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Deserialize;
use tempfile::TempDir;

const RESET: &str = "%{${reset_color}%}";

#[derive(Debug, Deserialize)]
struct FixtureFile {
    cases: Vec<FixtureCase>,
}

#[derive(Debug, Deserialize)]
struct FixtureCase {
    name: String,
    expected_stdout: String,
    #[serde(default = "default_repo")]
    target_repo: String,
    #[serde(default)]
    env: BTreeMap<String, String>,
    operations: Vec<Operation>,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum Operation {
    InitRepo {
        repo: String,
    },
    BareRemote {
        repo: String,
    },
    CloneRemote {
        repo: String,
        remote: String,
    },
    CommitFile {
        repo: String,
        path: String,
        contents: String,
        message: String,
    },
    WriteFile {
        repo: String,
        path: String,
        contents: String,
    },
    Git {
        repo: String,
        args: Vec<String>,
    },
    AddRemoteAndPush {
        repo: String,
        remote: String,
    },
}

#[test]
fn fixture_contract_matches_glint() {
    for path in fixture_files() {
        let contents = fs::read_to_string(&path).unwrap();
        let fixture: FixtureFile = serde_json::from_str(&contents).unwrap();

        for case in fixture.cases {
            let mut ctx = FixtureContext::default();
            for operation in case.operations {
                ctx.apply(operation);
            }

            let output = glint_output(ctx.repo(&case.target_repo), &case.env);
            let expected = render_expected(&case.expected_stdout, &ctx);
            assert_eq!(
                output,
                expected,
                "fixture {} in {}",
                case.name,
                path.display()
            );
        }
    }
}

#[derive(Default)]
struct FixtureContext {
    repos: BTreeMap<String, TempDir>,
}

impl FixtureContext {
    fn apply(&mut self, operation: Operation) {
        match operation {
            Operation::InitRepo { repo } => {
                let dir = self.ensure_repo(&repo);
                git(dir.path(), ["init", "-b", "main"]);
                git(dir.path(), ["config", "user.name", "glint-tests"]);
                git(
                    dir.path(),
                    ["config", "user.email", "glint-tests@example.com"],
                );
            }
            Operation::BareRemote { repo } => {
                let dir = self.ensure_repo(&repo);
                git_raw(["init", "--bare", dir.path().to_str().unwrap()]);
            }
            Operation::CloneRemote { repo, remote } => {
                let remote_path = self.repo(&remote).to_path_buf();
                let dir = self.ensure_repo(&repo);
                git_raw([
                    "clone",
                    "--branch",
                    "main",
                    remote_path.to_str().unwrap(),
                    dir.path().to_str().unwrap(),
                ]);
                git(dir.path(), ["config", "user.name", "glint-tests"]);
                git(
                    dir.path(),
                    ["config", "user.email", "glint-tests@example.com"],
                );
            }
            Operation::CommitFile {
                repo,
                path,
                contents,
                message,
            } => {
                let repo_path = self.repo(&repo).to_path_buf();
                write_file(&repo_path, &path, &contents);
                git(&repo_path, ["add", path.as_str()]);
                git(&repo_path, ["commit", "-m", message.as_str()]);
            }
            Operation::WriteFile {
                repo,
                path,
                contents,
            } => {
                let repo_path = self.repo(&repo).to_path_buf();
                write_file(&repo_path, &path, &contents);
            }
            Operation::Git { repo, args } => {
                let repo_path = self.repo(&repo).to_path_buf();
                git(&repo_path, args.iter().map(String::as_str));
            }
            Operation::AddRemoteAndPush { repo, remote } => {
                let repo_path = self.repo(&repo).to_path_buf();
                let remote_path = self.repo(&remote).to_path_buf();
                git(
                    &repo_path,
                    ["remote", "add", "origin", remote_path.to_str().unwrap()],
                );
                git(&repo_path, ["push", "-u", "origin", "main"]);
            }
        }
    }

    fn ensure_repo(&mut self, name: &str) -> &TempDir {
        self.repos
            .entry(name.to_owned())
            .or_insert_with(|| tempfile::tempdir().unwrap())
    }

    fn repo(&self, name: &str) -> &Path {
        self.repos.get(name).unwrap().path()
    }
}

fn default_repo() -> String {
    "repo".to_owned()
}

fn fixture_files() -> Vec<PathBuf> {
    let mut files = fs::read_dir("compat/fixtures")
        .unwrap()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.extension().and_then(|ext| ext.to_str()) == Some("json"))
        .collect::<Vec<_>>();
    files.sort();
    files
}

fn glint_output(repo: &Path, env_overrides: &BTreeMap<String, String>) -> String {
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

    for (key, value) in env_overrides {
        cmd.env(key, value);
    }

    let output = cmd.assert().success().get_output().stdout.clone();
    normalize_output(String::from_utf8(output).unwrap())
}

fn normalize_output(output: String) -> String {
    output.replace(RESET, "")
}

fn render_expected(template: &str, ctx: &FixtureContext) -> String {
    let mut rendered = template.to_owned();

    while let Some(start) = rendered.find("{{git_short_head:") {
        let rest = &rendered[start..];
        let end = rest.find("}}").unwrap();
        let token = &rest[..end + 2];
        let repo_name = token
            .trim_start_matches("{{git_short_head:")
            .trim_end_matches("}}");
        let value = git_output(ctx.repo(repo_name), ["rev-parse", "--short", "HEAD"]);
        rendered.replace_range(start..start + token.len(), value.trim());
    }

    rendered
}

fn write_file(repo: &Path, path: &str, contents: &str) {
    let full_path = repo.join(path);
    if let Some(parent) = full_path.parent() {
        fs::create_dir_all(parent).unwrap();
    }
    fs::write(full_path, contents).unwrap();
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
