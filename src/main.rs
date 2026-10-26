const USAGE: &str = "Usage: glint [--version | --help]";

fn main() {
    let mut args = std::env::args_os().skip(1);
    match (args.next(), args.next()) {
        (None, None) => print!("{}", glint::run(std::env::vars())),
        (Some(arg), None) if arg == "--version" || arg == "-V" => {
            println!("{} {}", env!("CARGO_PKG_NAME"), env!("CARGO_PKG_VERSION"));
        }
        (Some(arg), None) if arg == "--help" || arg == "-h" => {
            println!("{USAGE}\n\nWith no arguments, print the Git prompt segment.");
        }
        _ => {
            eprintln!("{USAGE}");
            std::process::exit(2);
        }
    }
}
