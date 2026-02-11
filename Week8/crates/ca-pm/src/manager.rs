use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

use crate::error::{PromptError, Result};
use crate::template::{Template, TemplateContext, TemplateRenderer};

/// 权限模式
#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PermissionMode {
    /// 默认模式 - 需要审批
    #[default]
    Default,
    /// 接受编辑 - 自动批准编辑操作
    AcceptEdits,
    /// 计划模式 - 只读,相当于 ReadOnly
    Plan,
    /// 绕过权限检查 - 自动批准
    BypassPermissions,
}

/// 任务配置 (从 config.yml 加载)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskConfig {
    /// 是否使用 Agent preset (如 claude_code)
    #[serde(default)]
    pub preset: bool,

    /// 允许的工具列表 (空 = 全部)
    #[serde(default)]
    pub tools: Vec<String>,

    /// 禁止的工具列表
    #[serde(default)]
    pub disallowed_tools: Vec<String>,

    /// 权限模式
    #[serde(default)]
    pub permission_mode: PermissionMode,

    /// 最大轮次
    #[serde(default = "default_max_turns")]
    pub max_turns: usize,

    /// 预算限制 (USD)
    #[serde(default = "default_max_budget")]
    pub max_budget_usd: f64,
}

impl Default for TaskConfig {
    fn default() -> Self {
        Self {
            preset: false,
            tools: Vec::new(),
            disallowed_tools: Vec::new(),
            permission_mode: PermissionMode::Default,
            max_turns: default_max_turns(),
            max_budget_usd: default_max_budget(),
        }
    }
}

fn default_max_turns() -> usize {
    20
}

fn default_max_budget() -> f64 {
    5.0
}

/// 任务模板 (3文件结构)
#[derive(Debug, Clone)]
pub struct TaskTemplate {
    /// 任务配置 (从 config.yml 加载)
    pub config: TaskConfig,
    /// 系统提示词模板 (从 system.jinja 加载, 可选)
    pub system_template: Option<String>,
    /// 用户提示词模板 (从 user.jinja 加载, 必需)
    pub user_template: String,
}

/// Prompt 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptConfig {
    /// 模板目录
    pub template_dir: PathBuf,

    /// 默认模板
    pub default_template: Option<String>,
}

impl Default for PromptConfig {
    fn default() -> Self {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        Self {
            template_dir: home.join(".code-agent").join("templates"),
            default_template: Some("default.jinja".to_string()),
        }
    }
}

/// Prompt 管理器
pub struct PromptManager {
    config: PromptConfig,
    renderer: TemplateRenderer,
    templates: HashMap<String, Template>,
}

impl PromptManager {
    /// 创建新的 Prompt 管理器
    pub fn new(config: PromptConfig) -> Result<Self> {
        let mut manager = Self {
            config,
            renderer: TemplateRenderer::new(),
            templates: HashMap::new(),
        };

        // 加载模板
        manager.load_templates()?;

        Ok(manager)
    }

    /// 加载所有模板
    fn load_templates(&mut self) -> Result<()> {
        if !self.config.template_dir.exists() {
            // 如果模板目录不存在,创建它并添加默认模板
            std::fs::create_dir_all(&self.config.template_dir)?;
            self.create_default_templates()?;
        }

        // 扫描模板目录
        if self.config.template_dir.is_dir() {
            for entry in std::fs::read_dir(&self.config.template_dir)? {
                let entry = entry?;
                let path = entry.path();

                if path.is_file()
                    && let Some(ext) = path.extension()
                    && (ext == "jinja" || ext == "j2")
                {
                    self.load_template(&path)?;
                }
            }
        }

        Ok(())
    }

    /// 加载单个模板
    fn load_template(&mut self, path: &Path) -> Result<()> {
        let content = std::fs::read_to_string(path)?;
        let name = path
            .file_stem()
            .and_then(|s| s.to_str())
            .ok_or_else(|| PromptError::Template("Invalid template name".to_string()))?
            .to_string();

        let template = Template {
            name: name.clone(),
            content,
            description: None,
        };

        // Add template to renderer
        self.renderer.add_template(template.clone())?;
        self.templates.insert(name, template);

        Ok(())
    }

    /// 创建默认模板
    fn create_default_templates(&self) -> Result<()> {
        let default_template = r#"# Task: {{ task }}

## Context
{% if context_files %}
The following files are relevant:
{% for file in context_files %}
- {{ file }}
{% endfor %}
{% endif %}

## Instructions
{{ instructions }}

## Output Format
Please provide:
1. A summary of the changes
2. The implementation details
3. Any potential issues or considerations
"#;

        let default_path = self.config.template_dir.join("default.jinja");
        std::fs::write(default_path, default_template)?;

        Ok(())
    }

    /// 渲染模板
    pub fn render(&self, template_name: &str, context: &TemplateContext) -> Result<String> {
        self.renderer.render(template_name, context)
    }

    /// 使用默认模板渲染
    pub fn render_default(&self, context: &TemplateContext) -> Result<String> {
        let template_name = self.config.default_template.as_deref().unwrap_or("default");

        self.render(template_name, context)
    }

    /// 直接渲染字符串
    pub fn render_str(&self, template_str: &str, context: &TemplateContext) -> Result<String> {
        self.renderer.render_str(template_str, context)
    }

    /// 列出所有模板
    pub fn list_templates(&self) -> Vec<&str> {
        self.templates.keys().map(|s| s.as_str()).collect()
    }

    /// 获取模板
    pub fn get_template(&self, name: &str) -> Option<&Template> {
        self.templates.get(name)
    }

    /// 验证模板语法
    pub fn validate_template(&self, template_name: &str) -> Result<bool> {
        self.templates.get(template_name).ok_or_else(|| {
            PromptError::Template(format!("Template not found: {}", template_name))
        })?;

        // 使用渲染器验证模板
        self.renderer.validate_template(template_name)
    }

    /// 验证所有模板
    pub fn validate_all_templates(&self) -> Result<Vec<String>> {
        let mut errors = Vec::new();

        for template_name in self.templates.keys() {
            if let Err(e) = self.validate_template(template_name) {
                errors.push(format!("{}: {}", template_name, e));
            }
        }

        if errors.is_empty() {
            Ok(vec![])
        } else {
            Ok(errors)
        }
    }

    /// 检查模板是否存在
    pub fn template_exists(&self, name: &str) -> bool {
        self.templates.contains_key(name)
    }

    /// 从目录加载任务模板 (支持 3 文件结构)
    ///
    /// # 目录结构
    ///
    /// ```text
    /// task_dir/
    /// ├── config.yml       # 任务配置 (可选, 如无则使用默认)
    /// ├── system.jinja     # 系统提示词 (可选)
    /// └── user.jinja       # 用户提示词 (必需)
    /// ```
    ///
    /// # 向后兼容
    ///
    /// - 如果 config.yml 不存在,使用默认配置
    /// - 如果 system.jinja 不存在,系统提示词为 None
    /// - user.jinja 是唯一必需的文件
    pub fn load_task_dir(&mut self, task_dir: &Path) -> Result<TaskTemplate> {
        // 1. 读取 config.yml (可选)
        let config_path = task_dir.join("config.yml");
        let config: TaskConfig = if config_path.exists() {
            let content = std::fs::read_to_string(&config_path).map_err(|e| {
                PromptError::Template(format!(
                    "Failed to read config.yml in {:?}: {}",
                    task_dir, e
                ))
            })?;
            serde_yaml::from_str(&content).map_err(|e| {
                PromptError::Template(format!(
                    "Failed to parse config.yml in {:?}: {}",
                    task_dir, e
                ))
            })?
        } else {
            TaskConfig::default() // 使用默认配置
        };

        // 2. 读取 system.jinja (可选)
        let system_path = task_dir.join("system.jinja");
        let system_template = if system_path.exists() {
            Some(std::fs::read_to_string(&system_path).map_err(|e| {
                PromptError::Template(format!(
                    "Failed to read system.jinja in {:?}: {}",
                    task_dir, e
                ))
            })?)
        } else {
            None
        };

        // 3. 读取 user.jinja (必需)
        let user_path = task_dir.join("user.jinja");
        if !user_path.exists() {
            return Err(PromptError::Template(format!(
                "user.jinja not found in {:?}",
                task_dir
            )));
        }
        let user_template = std::fs::read_to_string(&user_path).map_err(|e| {
            PromptError::Template(format!(
                "Failed to read user.jinja in {:?}: {}",
                task_dir, e
            ))
        })?;

        Ok(TaskTemplate {
            config,
            system_template,
            user_template,
        })
    }

    /// 渲染任务提示词
    ///
    /// # 返回值
    ///
    /// 返回元组 `(system_prompt, user_prompt)`:
    /// - `system_prompt`: 如果任务有 system.jinja,返回渲染后的系统提示词,否则为 None
    /// - `user_prompt`: 渲染后的用户提示词
    pub fn render_task(
        &self,
        task: &TaskTemplate,
        context: &TemplateContext,
    ) -> Result<(Option<String>, String)> {
        // 渲染 system prompt (如果有)
        let system = if let Some(ref tmpl) = task.system_template {
            Some(self.renderer.render_str(tmpl, context).map_err(|e| {
                PromptError::Template(format!("Failed to render system.jinja: {}", e))
            })?)
        } else {
            None
        };

        // 渲染 user prompt
        let user = self
            .renderer
            .render_str(&task.user_template, context)
            .map_err(|e| PromptError::Template(format!("Failed to render user.jinja: {}", e)))?;

        Ok((system, user))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_prompt_manager() {
        let config = PromptConfig::default();
        let manager = PromptManager::new(config).unwrap();

        let mut context = TemplateContext::new();
        context.insert("task", "Add a new feature").unwrap();
        context
            .insert("instructions", "Implement the feature carefully")
            .unwrap();

        let result = manager.render_str("Task: {{ task }}", &context).unwrap();
        assert_eq!(result, "Task: Add a new feature");
    }

    #[test]
    fn test_template_validation() {
        let config = PromptConfig::default();
        let manager = PromptManager::new(config).unwrap();

        // All default templates should be valid
        let errors = manager.validate_all_templates().unwrap();
        assert!(
            errors.is_empty(),
            "Template validation errors: {:?}",
            errors
        );
    }

    #[test]
    fn test_task_config_default() {
        let config = TaskConfig::default();
        assert!(!config.preset);
        assert!(config.tools.is_empty());
        assert!(config.disallowed_tools.is_empty());
        assert_eq!(config.permission_mode, PermissionMode::Default);
        assert_eq!(config.max_turns, 20);
        assert_eq!(config.max_budget_usd, 5.0);
    }

    #[test]
    fn test_task_config_deserialization() {
        let yaml = r#"
preset: true
tools:
  - Read
  - Write
disallowed_tools:
  - Delete
permission_mode: bypass_permissions
max_turns: 10
max_budget_usd: 2.5
"#;
        let config: TaskConfig = serde_yaml::from_str(yaml).unwrap();
        assert!(config.preset);
        assert_eq!(config.tools, vec!["Read", "Write"]);
        assert_eq!(config.disallowed_tools, vec!["Delete"]);
        assert_eq!(config.permission_mode, PermissionMode::BypassPermissions);
        assert_eq!(config.max_turns, 10);
        assert_eq!(config.max_budget_usd, 2.5);
    }

    #[test]
    fn test_permission_mode_default() {
        let mode = PermissionMode::default();
        assert_eq!(mode, PermissionMode::Default);
    }

    #[test]
    fn test_load_task_dir_with_all_files() {
        use std::fs;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let task_dir = temp_dir.path().join("test_task");
        fs::create_dir(&task_dir).unwrap();

        // 创建 config.yml
        fs::write(
            task_dir.join("config.yml"),
            r#"
preset: true
tools: []
disallowed_tools:
  - Write
permission_mode: default
max_turns: 15
max_budget_usd: 3.5
"#,
        )
        .unwrap();

        // 创建 system.jinja
        fs::write(
            task_dir.join("system.jinja"),
            "System prompt for {{ task_name }}",
        )
        .unwrap();

        // 创建 user.jinja
        fs::write(
            task_dir.join("user.jinja"),
            "User prompt for {{ task_name }}",
        )
        .unwrap();

        let mut manager = PromptManager::new(PromptConfig::default()).unwrap();
        let task_template = manager.load_task_dir(&task_dir).unwrap();

        // 验证 config
        assert!(task_template.config.preset);
        assert_eq!(task_template.config.disallowed_tools, vec!["Write"]);
        assert_eq!(task_template.config.max_turns, 15);
        assert_eq!(task_template.config.max_budget_usd, 3.5);

        // 验证模板
        assert!(task_template.system_template.is_some());
        assert_eq!(
            task_template.system_template.unwrap(),
            "System prompt for {{ task_name }}"
        );
        assert_eq!(
            task_template.user_template,
            "User prompt for {{ task_name }}"
        );
    }

    #[test]
    fn test_load_task_dir_minimal() {
        use std::fs;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let task_dir = temp_dir.path().join("test_task_minimal");
        fs::create_dir(&task_dir).unwrap();

        // 只创建 user.jinja (最小配置)
        fs::write(task_dir.join("user.jinja"), "Minimal user prompt").unwrap();

        let mut manager = PromptManager::new(PromptConfig::default()).unwrap();
        let task_template = manager.load_task_dir(&task_dir).unwrap();

        // 验证使用默认配置
        assert!(!task_template.config.preset);
        assert_eq!(task_template.config.max_turns, 20);
        assert_eq!(task_template.config.max_budget_usd, 5.0);

        // 验证没有 system template
        assert!(task_template.system_template.is_none());

        // 验证 user template
        assert_eq!(task_template.user_template, "Minimal user prompt");
    }

    #[test]
    fn test_load_task_dir_missing_user_jinja() {
        use std::fs;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let task_dir = temp_dir.path().join("test_task_invalid");
        fs::create_dir(&task_dir).unwrap();

        // 只创建 config.yml, 没有 user.jinja
        fs::write(task_dir.join("config.yml"), "preset: true").unwrap();

        let mut manager = PromptManager::new(PromptConfig::default()).unwrap();
        let result = manager.load_task_dir(&task_dir);

        // 应该返回错误
        assert!(result.is_err());
        assert!(
            result
                .unwrap_err()
                .to_string()
                .contains("user.jinja not found")
        );
    }

    #[test]
    fn test_render_task_with_system() {
        use std::fs;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let task_dir = temp_dir.path().join("test_task_render");
        fs::create_dir(&task_dir).unwrap();

        fs::write(task_dir.join("config.yml"), "preset: true").unwrap();
        fs::write(
            task_dir.join("system.jinja"),
            "System: Task is {{ task_name }}",
        )
        .unwrap();
        fs::write(task_dir.join("user.jinja"), "User: Do {{ action }}").unwrap();

        let mut manager = PromptManager::new(PromptConfig::default()).unwrap();
        let task_template = manager.load_task_dir(&task_dir).unwrap();

        let mut context = TemplateContext::new();
        context.insert("task_name", "test").unwrap();
        context.insert("action", "something").unwrap();

        let (system, user) = manager.render_task(&task_template, &context).unwrap();

        assert!(system.is_some());
        assert_eq!(system.unwrap(), "System: Task is test");
        assert_eq!(user, "User: Do something");
    }

    #[test]
    fn test_render_task_without_system() {
        use std::fs;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let task_dir = temp_dir.path().join("test_task_render_no_system");
        fs::create_dir(&task_dir).unwrap();

        fs::write(task_dir.join("user.jinja"), "User: Do {{ action }}").unwrap();

        let mut manager = PromptManager::new(PromptConfig::default()).unwrap();
        let task_template = manager.load_task_dir(&task_dir).unwrap();

        let mut context = TemplateContext::new();
        context.insert("action", "something").unwrap();

        let (system, user) = manager.render_task(&task_template, &context).unwrap();

        assert!(system.is_none());
        assert_eq!(user, "User: Do something");
    }
}
