//! Init 命令实现
//!
//! 提供交互式配置向导和 Agent 连接测试

use ca_core::{AgentConfig, AgentFactory, AgentType};
use std::io::{self, Write};

use crate::config::AppConfig;

/// 执行 init 命令
pub async fn execute_init(
    api_key: Option<String>,
    agent_type_str: Option<String>,
    interactive: bool,
    config: &AppConfig,
) -> anyhow::Result<()> {
    println!("🚀 欢迎使用 Code Agent!");
    println!();

    let mut new_config = config.clone();

    // 交互式模式
    if interactive {
        println!("开始配置向导...");
        println!();

        // 选择 Agent 类型
        let agent_type = if let Some(agent) = agent_type_str {
            parse_agent_type(&agent)?
        } else {
            select_agent_type()?
        };

        new_config.agent.agent_type = format!("{:?}", agent_type).to_lowercase();

        // 输入 API Key
        let api_key = if let Some(key) = api_key {
            key
        } else {
            input_api_key(&agent_type)?
        };

        new_config.agent.api_key = api_key.clone();

        // 选择模型
        let model = select_model(&agent_type)?;
        new_config.agent.model = model;

        // 测试连接
        println!();
        println!("🔌 测试 Agent 连接...");
        
        match test_connection(&agent_type, &api_key, &new_config.agent.model).await {
            Ok(true) => {
                println!("✅ 连接成功!");
            }
            Ok(false) => {
                println!("⚠️  连接验证失败,但配置将被保存");
                println!("   请检查 API Key 是否正确");
            }
            Err(e) => {
                println!("❌ 连接测试失败: {}", e);
                println!("   配置将被保存,但可能需要修正");
            }
        }
    } else {
        // 非交互模式
        if let Some(agent) = agent_type_str {
            new_config.agent.agent_type = agent;
        }

        if let Some(key) = api_key {
            new_config.agent.api_key = key;
        } else if new_config.agent.api_key.is_empty() {
            println!("⚠️  警告: 未设置 API 密钥");
            println!("   请使用 --api-key 参数或运行交互模式: code-agent init --interactive");
            println!();
        }
    }

    // 保存配置
    new_config.save_default()?;

    println!();
    println!("✅ 配置已保存!");
    println!("📁 配置位置: ~/.code-agent/config.toml");
    println!("📝 Agent 类型: {}", new_config.agent.agent_type);
    println!("📝 模型: {}", new_config.agent.model);
    println!();
    println!("🎉 初始化完成! 现在可以运行:");
    println!("   code-agent plan <feature-name>");
    println!("   code-agent run <feature-name>");

    Ok(())
}

/// 选择 Agent 类型
fn select_agent_type() -> anyhow::Result<AgentType> {
    println!("选择 Agent 类型:");
    println!("  1. Claude Agent (Tier 1: 完全支持)");
    println!("  2. Cursor Agent (Tier 2: 基础支持) - 即将推出");
    println!("  3. GitHub Copilot Agent (Tier 3: 实验性) - 即将推出");
    print!("\n请选择 [1-3] (默认: 1): ");
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    let choice = input.trim();

    match choice {
        "" | "1" => Ok(AgentType::Claude),
        "2" => {
            println!("⚠️  Cursor Agent 尚未实现,使用 Claude Agent");
            Ok(AgentType::Claude)
        }
        "3" => {
            println!("⚠️  Copilot Agent 尚未实现,使用 Claude Agent");
            Ok(AgentType::Claude)
        }
        _ => {
            anyhow::bail!("无效的选择: {}", choice);
        }
    }
}

/// 输入 API Key
fn input_api_key(agent_type: &AgentType) -> anyhow::Result<String> {
    let env_var = agent_type.primary_env_var();
    
    // 先检查环境变量
    if let Ok(key) = std::env::var(env_var) {
        println!("✓ 从环境变量 {} 检测到 API Key", env_var);
        print!("使用此 Key? [Y/n]: ");
        io::stdout().flush()?;

        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        
        if input.trim().is_empty() || input.trim().to_lowercase() == "y" {
            return Ok(key);
        }
    }

    println!();
    println!("请输入 {} API Key:", match agent_type {
        AgentType::Claude => "Anthropic",
        AgentType::Cursor => "Cursor",
        AgentType::Copilot => "GitHub",
    });
    println!("提示: 也可以设置环境变量 {}", env_var);
    print!("API Key: ");
    io::stdout().flush()?;

    let mut api_key = String::new();
    io::stdin().read_line(&mut api_key)?;
    let api_key = api_key.trim().to_string();

    if api_key.is_empty() {
        anyhow::bail!("API Key 不能为空");
    }

    Ok(api_key)
}

/// 选择模型
fn select_model(agent_type: &AgentType) -> anyhow::Result<String> {
    let default_model = match agent_type {
        AgentType::Claude => "claude-3-5-sonnet-20241022",
        AgentType::Cursor => "claude-4-5-sonnet",
        AgentType::Copilot => "gpt-4",
    };

    println!();
    print!("模型名称 (默认: {}): ", default_model);
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;
    let model = input.trim();

    if model.is_empty() {
        Ok(default_model.to_string())
    } else {
        Ok(model.to_string())
    }
}

/// 测试 Agent 连接
async fn test_connection(agent_type: &AgentType, api_key: &str, model: &str) -> anyhow::Result<bool> {
    let config = AgentConfig {
        agent_type: *agent_type,
        api_key: api_key.to_string(),
        model: Some(model.to_string()),
        api_url: None,
    };

    let agent = AgentFactory::create(config)?;
    
    agent.validate().await.map_err(|e| {
        anyhow::anyhow!("连接验证失败: {}", e)
    })
}

/// 解析 Agent 类型字符串
fn parse_agent_type(s: &str) -> anyhow::Result<AgentType> {
    match s.to_lowercase().as_str() {
        "claude" => Ok(AgentType::Claude),
        "cursor" => Ok(AgentType::Cursor),
        "copilot" => Ok(AgentType::Copilot),
        _ => anyhow::bail!("不支持的 Agent 类型: {}", s),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_agent_type() {
        assert!(matches!(parse_agent_type("claude").unwrap(), AgentType::Claude));
        assert!(matches!(parse_agent_type("Claude").unwrap(), AgentType::Claude));
        assert!(matches!(parse_agent_type("CLAUDE").unwrap(), AgentType::Claude));
        
        assert!(parse_agent_type("invalid").is_err());
    }
}
