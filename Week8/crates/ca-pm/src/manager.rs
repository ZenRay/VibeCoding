use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

use crate::error::{PromptError, Result};
use crate::template::{Template, TemplateContext, TemplateRenderer};

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
}
