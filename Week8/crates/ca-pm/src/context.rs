use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

use crate::error::Result;

/// Context Builder - 用于构建 Agent 请求的上下文
#[derive(Debug, Clone, Default)]
pub struct ContextBuilder {
    /// 文件列表
    files: Vec<FileContext>,
    /// 变量
    variables: HashMap<String, Value>,
    /// 指令
    instructions: Vec<String>,
    /// 项目信息
    project_info: Option<ProjectInfo>,
}

/// 文件上下文
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileContext {
    /// 文件路径
    pub path: String,
    /// 文件内容
    pub content: String,
    /// 文件语言
    pub language: Option<String>,
}

/// 项目信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectInfo {
    /// 项目名称
    pub name: String,
    /// 项目路径
    pub repo_path: String,
    /// 主要编程语言
    pub primary_language: Option<String>,
    /// 框架
    pub framework: Option<String>,
}

impl ContextBuilder {
    /// 创建新的 ContextBuilder
    pub fn new() -> Self {
        Self::default()
    }

    /// 添加文件
    pub fn add_file<P: Into<String>, C: Into<String>>(mut self, path: P, content: C) -> Self {
        self.files.push(FileContext {
            path: path.into(),
            content: content.into(),
            language: None,
        });
        self
    }

    /// 添加带语言的文件
    pub fn add_file_with_language<P: Into<String>, C: Into<String>, L: Into<String>>(
        mut self,
        path: P,
        content: C,
        language: L,
    ) -> Self {
        self.files.push(FileContext {
            path: path.into(),
            content: content.into(),
            language: Some(language.into()),
        });
        self
    }

    /// 添加变量
    pub fn add_variable<K: Into<String>, V: Serialize>(mut self, key: K, value: V) -> Result<Self> {
        let value = serde_json::to_value(value)?;
        self.variables.insert(key.into(), value);
        Ok(self)
    }

    /// 添加指令
    pub fn add_instruction<I: Into<String>>(mut self, instruction: I) -> Self {
        self.instructions.push(instruction.into());
        self
    }

    /// 设置项目信息
    pub fn with_project_info(mut self, project_info: ProjectInfo) -> Self {
        self.project_info = Some(project_info);
        self
    }

    /// 构建 TemplateContext
    pub fn build(self) -> Result<crate::template::TemplateContext> {
        let mut context = crate::template::TemplateContext::new();

        // 添加文件
        if !self.files.is_empty() {
            context.insert("files", &self.files)?;
        }

        // 添加变量
        for (key, value) in self.variables {
            context.data.insert(key, value);
        }

        // 添加指令
        if !self.instructions.is_empty() {
            context.insert("instructions", self.instructions.join("\n"))?;
        }

        // 添加项目信息
        if let Some(project_info) = self.project_info {
            context.insert("project", &project_info)?;
        }

        Ok(context)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_context_builder() {
        let context = ContextBuilder::new()
            .add_file("test.rs", "fn main() {}")
            .add_instruction("Write clean code")
            .add_variable("task", "Test task")
            .unwrap()
            .build()
            .unwrap();

        assert!(context.get("files").is_some());
        assert!(context.get("instructions").is_some());
        assert!(context.get("task").is_some());
    }

    #[test]
    fn test_context_builder_with_project_info() {
        let project_info = ProjectInfo {
            name: "Test Project".to_string(),
            repo_path: "/path/to/repo".to_string(),
            primary_language: Some("Rust".to_string()),
            framework: None,
        };

        let context = ContextBuilder::new()
            .with_project_info(project_info)
            .build()
            .unwrap();

        assert!(context.get("project").is_some());
    }
}
