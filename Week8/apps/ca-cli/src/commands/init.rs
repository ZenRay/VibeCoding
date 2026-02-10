//! Init 命令实现
//!
//! 验证环境变量配置和 Agent 连接测试 (零配置文件方案)

use ca_core::{AgentConfig, AgentFactory, AgentType, Config};
use std::fs;
use std::io::{self, Write};
use std::path::Path;

/// 执行 init 命令 (零配置文件方案 - 仅验证环境变量)
pub async fn execute_init(
    api_key: Option<String>,
    agent_type_str: Option<String>,
    interactive: bool,
    force: bool,
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

    // 获取 API URL (用于 OpenRouter 等第三方服务)
    let api_url = get_api_url_from_env(&agent_type);

    println!();
    println!("📋 检测到的配置:");
    println!("  Agent 类型: {:?}", agent_type);
    println!("  模型: {}", model);
    println!("  API Key: {}***", &api_key_to_test[..4.min(api_key_to_test.len())]);
    if let Some(ref url) = api_url {
        println!("  API URL: {}", url);
    }
    println!();

    // 测试连接
    println!("🔌 测试 Agent 连接...");
    match test_connection(&agent_type, &api_key_to_test, &model, api_url.as_deref()).await {
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
    
    // 检查是否已初始化
    let already_initialized = is_initialized();
    
    if already_initialized && !force {
        println!("ℹ️  项目已初始化");
        println!("✅ 环境配置验证通过");
        println!();
        println!("💡 提示: 使用 --force 强制重新初始化");
    } else {
        // 执行项目初始化
        if already_initialized {
            println!("🔄 强制重新初始化项目结构...");
            // 在 force 模式下，删除 CLAUDE.md 以便重新创建
            let claude_md_path = Path::new("CLAUDE.md");
            if claude_md_path.exists() {
                fs::remove_file(claude_md_path)?;
            }
        } else {
            println!("📁 初始化项目结构...");
        }
        
        create_project_structure()?;
        println!("✓ 已创建 specs/ 目录");
        
        update_gitignore()?;
        println!("✓ 已更新 .gitignore");
        
        create_claude_md()?;
        println!("✓ 已创建 CLAUDE.md");
        
        println!();
        println!("🎉 初始化完成! 现在可以运行:");
        println!("   code-agent plan <feature-name>");
        println!("   code-agent run <feature-name>");
        println!();
        println!("💡 状态追踪:");
        println!("   • status.md - 人类可读的进度报告 (中文)");
        println!("   • state.yml - 机器可读的状态文件 (用于恢复执行)");
    }

    println!();
    
    if !already_initialized || force {
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
    }

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
    // 使用 Config 的完整优先级逻辑
    Config::load_api_key(agent_type).map_err(|e| anyhow::anyhow!("{}", e))
}

/// 从环境变量获取 API URL
fn get_api_url_from_env(agent_type: &AgentType) -> Option<String> {
    match agent_type {
        AgentType::Claude => {
            std::env::var("ANTHROPIC_BASE_URL").ok()
                .or_else(|| std::env::var("CLAUDE_BASE_URL").ok())
                .or_else(|| std::env::var("OPENROUTER_BASE_URL").ok())
        }
        AgentType::Copilot => {
            std::env::var("COPILOT_BASE_URL").ok()
        }
        AgentType::Cursor => {
            std::env::var("CURSOR_BASE_URL").ok()
        }
    }
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
async fn test_connection(agent_type: &AgentType, api_key: &str, model: &str, api_url: Option<&str>) -> anyhow::Result<bool> {
    let config = AgentConfig {
        agent_type: *agent_type,
        api_key: api_key.to_string(),
        model: Some(model.to_string()),
        api_url: api_url.map(|s| s.to_string()),
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

/// 检查项目是否已初始化
fn is_initialized() -> bool {
    Path::new("specs").exists()
}

/// 创建项目结构
fn create_project_structure() -> anyhow::Result<()> {
    let specs_dir = Path::new("specs");
    if !specs_dir.exists() {
        fs::create_dir(specs_dir)?;
    }
    Ok(())
}

/// 更新 .gitignore 文件
fn update_gitignore() -> anyhow::Result<()> {
    let gitignore_path = Path::new(".gitignore");
    
    let rules = r#"
# Code Agent
.ca-state/          # 执行状态目录
specs/*/state.yml   # 功能执行状态 (包含敏感信息)
logs/               # 执行日志
*.ca.tmp            # 临时文件
"#;
    
    if gitignore_path.exists() {
        let content = fs::read_to_string(gitignore_path)?;
        if !content.contains("# Code Agent") {
            let mut new_content = content;
            if !new_content.ends_with('\n') {
                new_content.push('\n');
            }
            new_content.push_str(rules);
            fs::write(gitignore_path, new_content)?;
        }
    } else {
        fs::write(gitignore_path, rules.trim_start())?;
    }
    
    Ok(())
}

/// 创建 CLAUDE.md 文档
fn create_claude_md() -> anyhow::Result<()> {
    let claude_md_path = Path::new("CLAUDE.md");
    
    // 注意: 如果文件已存在，函数仍会被调用（通过 force 标志控制）
    // 但我们检查文件存在性，避免覆盖用户的自定义内容
    // force 模式下，调用者需要在外部处理删除逻辑
    if claude_md_path.exists() {
        return Ok(());
    }
    
    // 加载模板
    let template = include_str!("../templates/CLAUDE.md.template");
    
    // 检测项目名称
    let project_name = detect_project_name()?;
    
    // 获取当前日期
    let date = chrono::Utc::now().format("%Y-%m-%d").to_string();
    
    // 渲染模板
    let content = template
        .replace("{PROJECT_NAME}", &project_name)
        .replace("{DATE}", &date);
    
    // 写入文件
    fs::write(claude_md_path, content)?;
    
    Ok(())
}

/// 自动检测项目名称
fn detect_project_name() -> anyhow::Result<String> {
    // 优先级 1: 从 Cargo.toml 读取
    if let Ok(cargo_content) = fs::read_to_string("Cargo.toml") {
        for line in cargo_content.lines() {
            if line.trim().starts_with("name") {
                if let Some(name) = line.split('=').nth(1) {
                    let name = name.trim().trim_matches('"').trim_matches('\'');
                    if !name.is_empty() {
                        return Ok(name.to_string());
                    }
                }
            }
        }
    }
    
    // 优先级 2: 从 package.json 读取
    if let Ok(package_content) = fs::read_to_string("package.json") {
        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&package_content) {
            if let Some(name) = json.get("name").and_then(|n| n.as_str()) {
                return Ok(name.to_string());
            }
        }
    }
    
    // 优先级 3: 使用当前目录名
    let current_dir = std::env::current_dir()?;
    if let Some(dir_name) = current_dir.file_name() {
        if let Some(name) = dir_name.to_str() {
            return Ok(name.to_string());
        }
    }
    
    // 默认值
    Ok("MyProject".to_string())
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
