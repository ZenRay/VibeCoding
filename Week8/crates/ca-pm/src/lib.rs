pub mod context;
pub mod error;
pub mod manager;
pub mod template;

pub use context::{ContextBuilder, FileContext, ProjectInfo};
pub use error::{PromptError, Result};
pub use manager::{PermissionMode, PromptConfig, PromptManager, TaskConfig, TaskTemplate};
pub use template::{Template, TemplateContext};
