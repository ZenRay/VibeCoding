//! Init 命令实现
//!
//! 验证环境变量配置和 Agent 连接测试 (零配置文件方案)

use ca_core::{AgentConfig, AgentFactory, AgentType};
use std::io::{self, Write};

/// 执行 init 命令 (零配置文件方案 - 仅验证环境变量)
pub async fn execute_init(
    api_key: Option<String>,
    agent_type_str: Option<String>,
    interactive: bool,
    _config: &crate::config::AppConfig,
) -> anyhow::Result<()> {
    println!("🚀 欢迎使用 Code Agent!");
    println!();
    println!("🔧 Code Agent 使用零配置文件方案 - 所有配置通过环境变量提供");
    println!();

    // 确定 Agent 类型
    let agent_type = if let Some(agent) = agent_type_str {
        parse_agent_type(&agent)?
    } else if interactive {
        select_agent_type()?
    } else {
        // 自动检测
        detect_agent_type_from_env()
    };

    // 获取 API Key
    let api_key_to_test = if let Some(key) = api_key {
        key
    } else if interactive {
        input_api_key(&agent_type)?
    } else {
        // 从环境变量获取
        get_api_key_from_env(&agent_type)?
    };

    // 获取模型
    let model = if interactive {
        select_model(&agent_type)?
    } else {
        get_default_model(&agent_type)
    };

    println!();
    println!("📋 检测到的配置:");
    println!("  Agent 类型: {:?}", agent_type);
    println!("  模型: {}", model);
    println!("  API Key: {}***", &api_key_to_test[..4.min(api_key_to_test.len())]);
    println!();

    // 测试连接
    println!("🔌 测试 Agent 连接...");
    match test_connection(&agent_type, &api_key_to_test, &model).await {
        Ok(true) => {
            println!("✅ 连接成功!");
        }
        Ok(false) => {
            println!("⚠️  连接验证失败");
            println!("   请检查 API Key 是否正确");
        }
        Err(e) => {
            println!("❌ 连接测试失败: {}", e);
        }
    }

    println!();
    println!("📝 如何设置环境变量:");
    println!();
    
    match agent_type {
        AgentType::Claude => {
            println!("  # Claude Agent (推荐使用 ANTHROPIC_API_KEY)");
            println!("  export ANTHROPIC_API_KEY='sk-ant-xxx'");
            println!();
            println!("  # 可选: 指定模型");
            println!("  export CLAUDE_MODEL='claude-3-5-sonnet-20241022'");
        }
        AgentType::Copilot => {
            println!("  # GitHub Copilot Agent");
            println!("  export COPILOT_GITHUB_TOKEN='ghp_xxx'");
            println!();
            println!("  # 可选: 指定模型");
            println!("  export COPILOT_MODEL='gpt-4'");
        }
        AgentType::Cursor => {
            println!("  # Cursor Agent");
            println!("  export CURSOR_API_KEY='cursor_xxx'");
            println!();
            println!("  # 可选: 指定模型");
            println!("  export CURSOR_MODEL='claude-4-5-sonnet'");
        }
    }

    println!();
    println!("💡 提示: 将上述命令添加到 ~/.bashrc 或 ~/.zshrc 以永久保存");
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

/// 从环境变量自动检测 Agent 类型
fn detect_agent_type_from_env() -> AgentType {
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

/// 从环境变量获取 API Key
fn get_api_key_from_env(agent_type: &AgentType) -> anyhow::Result<String> {
    let env_var = agent_type.primary_env_var();
    std::env::var(env_var).map_err(|_| {
        anyhow::anyhow!(
            "未设置环境变量 {}. 请运行: export {}='your-key'",
            env_var,
            env_var
        )
    })
}

/// 获取默认模型
fn get_default_model(agent_type: &AgentType) -> String {
    match agent_type {
        AgentType::Claude => {
            std::env::var("CLAUDE_MODEL")
                .or_else(|_| std::env::var("ANTHROPIC_MODEL"))
                .unwrap_or_else(|_| "claude-3-5-sonnet-20241022".to_string())
        }
        AgentType::Cursor => std::env::var("CURSOR_MODEL")
            .unwrap_or_else(|_| "claude-4-5-sonnet".to_string()),
        AgentType::Copilot => {
            std::env::var("COPILOT_MODEL").unwrap_or_else(|_| "gpt-4".to_string())
        }
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
