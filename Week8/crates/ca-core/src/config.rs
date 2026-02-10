use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use crate::agent::AgentType;
use crate::error::{CoreError, Result};

/// 运行时配置 (仅存于内存,不保存到文件)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Agent 配置
    pub agent: AgentConfig,
    /// 项目配置
    pub project: ProjectConfig,
    /// 执行配置
    pub execution: ExecutionConfig,
}

/// Agent 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    /// Agent 类型
    pub agent_type: AgentType,
    /// API 密钥
    pub api_key: String,
    /// 模型名称
    pub model: Option<String>,
    /// API URL
    pub api_url: Option<String>,
}

/// 项目配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectConfig {
    /// 工作目录
    pub workspace_dir: PathBuf,
    /// Specs 目录
    pub specs_dir: PathBuf,
    /// 状态目录
    pub state_dir: PathBuf,
}

impl Default for ProjectConfig {
    fn default() -> Self {
        Self {
            workspace_dir: PathBuf::from("."),
            specs_dir: PathBuf::from("specs"),
            state_dir: PathBuf::from(".ca-state"),
        }
    }
}

/// 执行配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionConfig {
    /// 最大重试次数
    pub max_retries: u32,
    /// 自动备份
    pub auto_backup: bool,
    /// 启用恢复功能
    pub enable_resume: bool,
    /// 检查点间隔
    pub checkpoint_interval: u32,
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self {
            max_retries: 3,
            auto_backup: true,
            enable_resume: true,
            checkpoint_interval: 5,
        }
    }
}

impl Config {
    /// 从环境变量加载 (零配置文件)
    pub fn from_env() -> Result<Self> {
        let agent_type = Self::detect_agent_type();
        let api_key = Self::load_api_key(&agent_type)?;

        Ok(Self {
            agent: AgentConfig {
                agent_type,
                api_key,
                model: Self::load_model(&agent_type),
                api_url: None,
            },
            project: ProjectConfig::default(),
            execution: ExecutionConfig::default(),
        })
    }

    /// 自动检测 Agent 类型 (根据环境变量)
    fn detect_agent_type() -> AgentType {
        if std::env::var("ANTHROPIC_API_KEY").is_ok() || std::env::var("CLAUDE_API_KEY").is_ok() {
            return AgentType::Claude;
        }

        if std::env::var("COPILOT_GITHUB_TOKEN").is_ok()
            || std::env::var("GH_TOKEN").is_ok()
            || std::env::var("GITHUB_TOKEN").is_ok()
        {
            return AgentType::Copilot;
        }

        if std::env::var("CURSOR_API_KEY").is_ok() {
            return AgentType::Cursor;
        }

        AgentType::Claude // 默认
    }

    /// 加载 API Key (按官方环境变量)
    fn load_api_key(agent_type: &AgentType) -> Result<String> {
        match agent_type {
            AgentType::Claude => std::env::var("ANTHROPIC_API_KEY")
                .or_else(|_| std::env::var("CLAUDE_API_KEY"))
                .map_err(|_| {
                    CoreError::Config(
                        "API key not found. Set ANTHROPIC_API_KEY:\n  export ANTHROPIC_API_KEY='sk-ant-xxx'".to_string(),
                    )
                }),

            AgentType::Copilot => std::env::var("COPILOT_GITHUB_TOKEN")
                .or_else(|_| std::env::var("GH_TOKEN"))
                .or_else(|_| std::env::var("GITHUB_TOKEN"))
                .map_err(|_| {
                    CoreError::Config(
                        "GitHub token not found. Set COPILOT_GITHUB_TOKEN:\n  export COPILOT_GITHUB_TOKEN='ghp_xxx'".to_string(),
                    )
                }),

            AgentType::Cursor => std::env::var("CURSOR_API_KEY").map_err(|_| {
                CoreError::Config(
                    "API key not found. Set CURSOR_API_KEY:\n  export CURSOR_API_KEY='cursor_xxx'"
                        .to_string(),
                )
            }),
        }
    }

    /// 加载模型名称
    fn load_model(agent_type: &AgentType) -> Option<String> {
        match agent_type {
            AgentType::Claude => std::env::var("CLAUDE_MODEL")
                .or_else(|_| std::env::var("ANTHROPIC_MODEL"))
                .ok(),
            AgentType::Copilot => std::env::var("COPILOT_MODEL").ok(),
            AgentType::Cursor => std::env::var("CURSOR_MODEL").ok(),
        }
    }

    /// 验证配置
    pub fn validate(&self) -> Result<()> {
        if self.agent.api_key.is_empty() {
            return Err(CoreError::Config("API key is empty".to_string()));
        }

        if !self.project.workspace_dir.exists() {
            return Err(CoreError::Config(format!(
                "Workspace directory does not exist: {}",
                self.project.workspace_dir.display()
            )));
        }

        Ok(())
    }

    /// 与命令行参数合并
    pub fn merge_with_cli_args(
        &mut self,
        agent_type: Option<AgentType>,
        api_key: Option<String>,
        model: Option<String>,
    ) {
        if let Some(api_key) = api_key {
            self.agent.api_key = api_key;
        }

        if let Some(agent_type) = agent_type {
            self.agent.agent_type = agent_type;
            // 如果改变了 Agent 类型,尝试重新加载 API key
            if let Ok(api_key) = Self::load_api_key(&agent_type) {
                self.agent.api_key = api_key;
            }
        }

        if let Some(model) = model {
            self.agent.model = Some(model);
        }
    }

    /// 显示配置信息
    pub fn display(&self) -> String {
        let mut output = String::new();
        output.push_str("🔧 Current Configuration\n\n");
        output.push_str(&format!("Agent Type: {:?}\n", self.agent.agent_type));

        // 隐藏 API key 的大部分内容
        let api_key_display = if self.agent.api_key.len() > 8 {
            format!(
                "{}***{}",
                &self.agent.api_key[..4],
                &self.agent.api_key[self.agent.api_key.len() - 4..]
            )
        } else {
            "***".to_string()
        };
        output.push_str(&format!("API Key: {}\n", api_key_display));

        if let Some(ref model) = self.agent.model {
            output.push_str(&format!("Model: {}\n", model));
        } else {
            output.push_str("Model: (using default)\n");
        }

        output.push_str("\n📝 Environment Variables:\n");
        for var_name in self.agent.agent_type.env_var_names() {
            if let Ok(value) = std::env::var(var_name) {
                let value_display = if value.len() > 8 {
                    format!("{}***", &value[..4])
                } else {
                    "***".to_string()
                };
                output.push_str(&format!("  ✅ {} = {}\n", var_name, value_display));
            } else {
                output.push_str(&format!("  ❌ {} = (not set)\n", var_name));
            }
        }

        output
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_agent_type() {
        let agent_type = Config::detect_agent_type();
        // 默认应该是 Claude
        assert_eq!(agent_type, AgentType::Claude);
    }

    #[test]
    fn test_project_config_default() {
        let config = ProjectConfig::default();
        assert_eq!(config.workspace_dir, PathBuf::from("."));
        assert_eq!(config.specs_dir, PathBuf::from("specs"));
        assert_eq!(config.state_dir, PathBuf::from(".ca-state"));
    }

    #[test]
    fn test_execution_config_default() {
        let config = ExecutionConfig::default();
        assert_eq!(config.max_retries, 3);
        assert!(config.auto_backup);
        assert!(config.enable_resume);
        assert_eq!(config.checkpoint_interval, 5);
    }
}
