mod git;
mod render;

use std::ffi::OsString;

pub use git::GitStatus;
pub use render::PromptTheme;

pub fn run<I, K, V>(env: I) -> String
where
    I: IntoIterator<Item = (K, V)>,
    K: Into<OsString>,
    V: Into<OsString>,
{
    let theme = PromptTheme::from_env(env);

    match git::collect_status() {
        Some(status) => render::render(&status, &theme),
        None => String::new(),
    }
}
