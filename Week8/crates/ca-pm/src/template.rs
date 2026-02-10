use minijinja::Environment;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::error::Result;

/// 模板
#[derive(Debug, Clone)]
pub struct Template {
    /// 模板名称
    pub name: String,

    /// 模板内容
    pub content: String,

    /// 模板描述
    pub description: Option<String>,
}

/// 模板上下文
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateContext {
    /// 上下文数据
    #[serde(flatten)]
    pub data: serde_json::Map<String, Value>,
}

impl TemplateContext {
    /// 创建新的上下文
    pub fn new() -> Self {
        Self {
            data: serde_json::Map::new(),
        }
    }

    /// 插入值
    pub fn insert<K: Into<String>, V: Serialize>(&mut self, key: K, value: V) -> Result<()> {
        let value = serde_json::to_value(value)?;
        self.data.insert(key.into(), value);
        Ok(())
    }

    /// 获取值
    pub fn get(&self, key: &str) -> Option<&Value> {
        self.data.get(key)
    }

    /// 从 JSON 字符串创建
    pub fn from_json(json: &str) -> Result<Self> {
        Ok(serde_json::from_str(json)?)
    }
}

impl Default for TemplateContext {
    fn default() -> Self {
        Self::new()
    }
}

/// 模板渲染器
pub struct TemplateRenderer {
    env: Environment<'static>,
}

impl TemplateRenderer {
    /// 创建新的渲染器
    pub fn new() -> Self {
        let mut env = Environment::new();

        // 配置 MiniJinja 环境
        env.set_trim_blocks(true);
        env.set_lstrip_blocks(true);

        Self { env }
    }

    /// 添加模板(使用字符串 slice)
    pub fn add_template_str(&mut self, name: &str, content: &str) -> Result<()> {
        // MiniJinja 的 add_template 需要 'static 生命周期
        // 所以我们使用 add_template 但通过 String leak 来实现
        let name_static: &'static str = Box::leak(name.to_string().into_boxed_str());
        let content_static: &'static str = Box::leak(content.to_string().into_boxed_str());
        self.env.add_template(name_static, content_static)?;
        Ok(())
    }

    /// 添加模板
    pub fn add_template(&mut self, template: Template) -> Result<()> {
        self.add_template_str(&template.name, &template.content)
    }

    /// 渲染模板
    pub fn render(&self, template_name: &str, context: &TemplateContext) -> Result<String> {
        let tmpl = self.env.get_template(template_name)?;
        let result = tmpl.render(&context.data)?;
        Ok(result)
    }

    /// 直接渲染字符串模板
    pub fn render_str(&self, template_str: &str, context: &TemplateContext) -> Result<String> {
        let result = self.env.render_str(template_str, &context.data)?;
        Ok(result)
    }

    /// 验证模板是否存在且有效
    pub fn validate_template(&self, template_name: &str) -> Result<bool> {
        match self.env.get_template(template_name) {
            Ok(_) => Ok(true),
            Err(e) => Err(crate::error::PromptError::Template(format!(
                "Template validation failed: {}",
                e
            ))),
        }
    }
}

impl Default for TemplateRenderer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_template_rendering() {
        let mut renderer = TemplateRenderer::new();

        let template = Template {
            name: "test".to_string(),
            content: "Hello {{ name }}!".to_string(),
            description: None,
        };

        renderer.add_template(template).unwrap();

        let mut context = TemplateContext::new();
        context.insert("name", "World").unwrap();

        let result = renderer.render("test", &context).unwrap();
        assert_eq!(result, "Hello World!");
    }

    #[test]
    fn test_render_str() {
        let renderer = TemplateRenderer::new();

        let mut context = TemplateContext::new();
        context.insert("name", "Rust").unwrap();

        let result = renderer.render_str("Hello {{ name }}!", &context).unwrap();
        assert_eq!(result, "Hello Rust!");
    }
}
