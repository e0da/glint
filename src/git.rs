use std::process::Command;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GitStatus {
    pub branch: String,
    pub ahead: usize,
    pub behind: usize,
    pub staged: usize,
    pub conflicts: usize,
    pub changed: usize,
    pub untracked: usize,
}

pub fn collect_status() -> Option<GitStatus> {
    let output = Command::new("git")
        .args(["status", "--porcelain=v2", "--branch"])
        .output()
        .ok()?;

    if !output.status.success() {
        return None;
    }

    parse_status(&String::from_utf8_lossy(&output.stdout))
}

fn parse_status(output: &str) -> Option<GitStatus> {
    let mut branch_name = None;
    let mut branch_oid = None;
    let mut ahead = 0;
    let mut behind = 0;
    let mut staged = 0;
    let mut conflicts = 0;
    let mut changed = 0;
    let mut untracked = 0;

    for line in output.lines() {
        if let Some(head) = line.strip_prefix("# branch.head ") {
            branch_name = Some(head.to_owned());
            continue;
        }

        if let Some(oid) = line.strip_prefix("# branch.oid ") {
            branch_oid = Some(oid.to_owned());
            continue;
        }

        if let Some(ab) = line.strip_prefix("# branch.ab ") {
            for part in ab.split_whitespace() {
                if let Some(value) = part.strip_prefix('+') {
                    ahead = value.parse().ok()?;
                } else if let Some(value) = part.strip_prefix('-') {
                    behind = value.parse().ok()?;
                }
            }
            continue;
        }

        if line.starts_with("? ") {
            untracked += 1;
            continue;
        }

        if let Some(record) = line.strip_prefix("1 ") {
            let xy = record.split_whitespace().next()?;
            let (index, worktree) = xy.split_at(1);

            if is_changed(index) {
                staged += 1;
            }

            if is_changed(worktree) {
                changed += 1;
            }

            continue;
        }

        if let Some(record) = line.strip_prefix("2 ") {
            let xy = record.split_whitespace().next()?;
            let (index, worktree) = xy.split_at(1);

            if is_changed(index) {
                staged += 1;
            }

            if is_changed(worktree) {
                changed += 1;
            }

            continue;
        }

        if line.starts_with("u ") {
            conflicts += 1;
        }
    }

    let branch = match branch_name.as_deref() {
        Some("(detached)") => format!(":{}", short_oid(branch_oid.as_deref())?),
        Some(name) => name.to_owned(),
        _ => return None,
    };

    Some(GitStatus {
        branch,
        ahead,
        behind,
        staged,
        conflicts,
        changed,
        untracked,
    })
}

fn short_oid(oid: Option<&str>) -> Option<&str> {
    let value = oid?;

    if value == "(initial)" || value.len() < 7 {
        return None;
    }

    value.get(..7)
}

fn is_changed(value: &str) -> bool {
    !matches!(value, "." | " ")
}

#[cfg(test)]
mod tests {
    use super::{GitStatus, parse_status};

    #[test]
    fn parses_branch_and_counts() {
        let status = parse_status(
            "\
# branch.oid aabbccddeeff00112233445566778899aabbccdd
# branch.head main
# branch.upstream origin/main
# branch.ab +2 -1
1 M. N... 100644 100644 100644 abcdef1 abcdef2 src/lib.rs
1 .M N... 100644 100644 100644 abcdef1 abcdef1 src/main.rs
2 MM N... 100644 100644 100644 100644 abcdef1 abcdef2 R100 src/old.rs\tsrc/new.rs
u UU N... 100644 100644 100644 100644 abcdef1 abcdef2 abcdef3 conflicted.rs
? untracked.rs
",
        )
        .unwrap();

        assert_eq!(
            status,
            GitStatus {
                branch: "main".to_owned(),
                ahead: 2,
                behind: 1,
                staged: 2,
                conflicts: 1,
                changed: 2,
                untracked: 1,
            }
        );
    }

    #[test]
    fn parses_detached_head() {
        let status = parse_status(
            "\
# branch.oid 70c2952abcdef012345678901234567890123456
# branch.head (detached)
",
        )
        .unwrap();

        assert_eq!(status.branch, ":70c2952");
    }

    #[test]
    fn ignores_non_git_output() {
        assert!(parse_status("").is_none());
    }
}
