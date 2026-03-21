use std::collections::HashMap;
use std::ffi::OsString;

use crate::GitStatus;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PromptTheme {
    pub prefix: String,
    pub suffix: String,
    pub separator: String,
    pub branch: String,
    pub staged: String,
    pub conflicts: String,
    pub changed: String,
    pub behind: String,
    pub ahead: String,
    pub untracked: String,
    pub clean: String,
    pub reset: String,
}

impl Default for PromptTheme {
    fn default() -> Self {
        Self {
            prefix: "(".to_owned(),
            suffix: ")".to_owned(),
            separator: "|".to_owned(),
            branch: "%{$fg_bold[magenta]%}".to_owned(),
            staged: "%{$fg[red]%}%{●%G%}".to_owned(),
            conflicts: "%{$fg[red]%}%{✖%G%}".to_owned(),
            changed: "%{$fg[blue]%}%{✚%G%}".to_owned(),
            behind: "%{↓%G%}".to_owned(),
            ahead: "%{↑%G%}".to_owned(),
            untracked: "%{…%G%}".to_owned(),
            clean: "%{$fg_bold[green]%}%{✔%G%}".to_owned(),
            reset: "%{${reset_color}%}".to_owned(),
        }
    }
}

impl PromptTheme {
    pub fn from_env<I, K, V>(env: I) -> Self
    where
        I: IntoIterator<Item = (K, V)>,
        K: Into<OsString>,
        V: Into<OsString>,
    {
        let mut theme = Self::default();
        let vars = env
            .into_iter()
            .filter_map(|(key, value)| {
                Some((
                    key.into().into_string().ok()?,
                    value.into().into_string().ok()?,
                ))
            })
            .collect::<HashMap<_, _>>();

        apply_override(&mut theme.prefix, &vars, "ZSH_THEME_GIT_PROMPT_PREFIX");
        apply_override(&mut theme.suffix, &vars, "ZSH_THEME_GIT_PROMPT_SUFFIX");
        apply_override(
            &mut theme.separator,
            &vars,
            "ZSH_THEME_GIT_PROMPT_SEPARATOR",
        );
        apply_override(&mut theme.branch, &vars, "ZSH_THEME_GIT_PROMPT_BRANCH");
        apply_override(&mut theme.staged, &vars, "ZSH_THEME_GIT_PROMPT_STAGED");
        apply_override(
            &mut theme.conflicts,
            &vars,
            "ZSH_THEME_GIT_PROMPT_CONFLICTS",
        );
        apply_override(&mut theme.changed, &vars, "ZSH_THEME_GIT_PROMPT_CHANGED");
        apply_override(&mut theme.behind, &vars, "ZSH_THEME_GIT_PROMPT_BEHIND");
        apply_override(&mut theme.ahead, &vars, "ZSH_THEME_GIT_PROMPT_AHEAD");
        apply_override(
            &mut theme.untracked,
            &vars,
            "ZSH_THEME_GIT_PROMPT_UNTRACKED",
        );
        apply_override(&mut theme.clean, &vars, "ZSH_THEME_GIT_PROMPT_CLEAN");

        theme
    }
}

pub fn render(status: &GitStatus, theme: &PromptTheme) -> String {
    let mut output = format!(
        "{}{}{}{}",
        theme.prefix, theme.branch, status.branch, theme.reset
    );

    if status.behind > 0 {
        output.push_str(&format!("{}{}{}", theme.behind, status.behind, theme.reset));
    }

    if status.ahead > 0 {
        output.push_str(&format!("{}{}{}", theme.ahead, status.ahead, theme.reset));
    }

    output.push_str(&theme.separator);

    if status.staged > 0 {
        output.push_str(&format!("{}{}{}", theme.staged, status.staged, theme.reset));
    }

    if status.conflicts > 0 {
        output.push_str(&format!(
            "{}{}{}",
            theme.conflicts, status.conflicts, theme.reset
        ));
    }

    if status.changed > 0 {
        output.push_str(&format!(
            "{}{}{}",
            theme.changed, status.changed, theme.reset
        ));
    }

    if status.untracked > 0 {
        output.push_str(&format!("{}{}", theme.untracked, theme.reset));
    }

    if status.staged == 0 && status.conflicts == 0 && status.changed == 0 && status.untracked == 0 {
        output.push_str(&theme.clean);
    }

    output.push_str(&theme.reset);
    output.push_str(&theme.suffix);
    output
}

fn apply_override(field: &mut String, vars: &HashMap<String, String>, key: &str) {
    if let Some(value) = vars.get(key) {
        *field = value.clone();
    }
}

#[cfg(test)]
mod tests {
    use crate::GitStatus;

    use super::{PromptTheme, render};

    fn status() -> GitStatus {
        GitStatus {
            branch: "main".to_owned(),
            ahead: 2,
            behind: 1,
            staged: 3,
            conflicts: 4,
            changed: 5,
            untracked: 1,
        }
    }

    #[test]
    fn renders_full_status() {
        let theme = PromptTheme {
            prefix: "(".to_owned(),
            suffix: ")".to_owned(),
            separator: "|".to_owned(),
            branch: "BR".to_owned(),
            staged: "S".to_owned(),
            conflicts: "C".to_owned(),
            changed: "M".to_owned(),
            behind: "B".to_owned(),
            ahead: "A".to_owned(),
            untracked: "U".to_owned(),
            clean: "K".to_owned(),
            reset: "R".to_owned(),
        };

        assert_eq!(render(&status(), &theme), "(BRmainRB1RA2R|S3RC4RM5RURR)");
    }

    #[test]
    fn renders_clean_status() {
        let theme = PromptTheme {
            branch: String::new(),
            staged: "S".to_owned(),
            conflicts: "C".to_owned(),
            changed: "M".to_owned(),
            behind: "B".to_owned(),
            ahead: "A".to_owned(),
            untracked: "U".to_owned(),
            clean: "K".to_owned(),
            reset: String::new(),
            ..PromptTheme::default()
        };
        let status = GitStatus {
            branch: "main".to_owned(),
            ahead: 0,
            behind: 0,
            staged: 0,
            conflicts: 0,
            changed: 0,
            untracked: 0,
        };

        assert_eq!(render(&status, &theme), "(main|K)");
    }
}
