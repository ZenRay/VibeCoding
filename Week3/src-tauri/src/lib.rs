pub mod audio;
pub mod config;
pub mod input;
pub mod network;
pub mod system;
pub mod ui;
pub mod utils;

pub fn app_version() -> &'static str {
    "0.1.0"
}

#[cfg(test)]
mod tests {
    use super::app_version;

    #[test]
    fn app_version_looks_like_semver() {
        assert!(app_version().contains('.'));
    }
}
