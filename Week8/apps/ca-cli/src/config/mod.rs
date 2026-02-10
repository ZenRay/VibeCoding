use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    /// Agent 配置
    pub agent: AgentConfig,

    /// Prompt 配置
    pub prompt: PromptConfig,

    /// 默认工作目录
    pub default_repo: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    /// Agent 类型 (claude, copilot, cursor)
    pub agent_type: String,

    /// API 密钥
    pub api_key: String,

    /// API URL (可选)
    pub api_url: Option<String>,

    /// 默认模型
    pub model: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptConfig {
    /// 模板目录
    pub template_dir: PathBuf,

    /// 默认模板
    pub default_template: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        let config_dir = home.join(".code-agent");

        Self {
            agent: AgentConfig {
                agent_type: "claude".to_string(),
                api_key: String::new(),
                api_url: None,
                model: "claude-3-5-sonnet-20241022".to_string(),
            },
            prompt: PromptConfig {
                template_dir: config_dir.join("templates"),
                default_template: "default".to_string(),
            },
            default_repo: None,
        }
    }
}

impl AppConfig {
    /// 加载配置文件
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Self = toml::from_str(&content)?;
        Ok(config)
    }

    /// 加载默认配置
    pub fn load_default() -> anyhow::Result<Self> {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        let config_path = home.join(".code-agent").join("config.toml");

        if config_path.exists() {
            Self::load_from_file(config_path)
        } else {
            Ok(Self::default())
        }
    }

    /// 保存配置文件
    pub fn save<P: AsRef<Path>>(&self, path: P) -> anyhow::Result<()> {
        let content = toml::to_string_pretty(self)?;

        // 确保目录存在
        if let Some(parent) = path.as_ref().parent() {
            std::fs::create_dir_all(parent)?;
        }

        std::fs::write(path, content)?;
        Ok(())
    }

    /// 保存到默认位置
    pub fn save_default(&self) -> anyhow::Result<()> {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        let config_path = home.join(".code-agent").join("config.toml");
        self.save(config_path)
    }
}
