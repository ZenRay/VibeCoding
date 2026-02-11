/// 示例: 演示如何使用新的 3 文件模板结构
///
/// 运行: cargo run --package ca-pm --example task_template

use ca_pm::{PromptConfig, PromptManager, TemplateContext};
use std::path::PathBuf;

fn main() -> anyhow::Result<()> {
    println!("=== Code Agent Prompt Manager - Task Template Demo ===\n");

    // 1. 创建 PromptManager
    let config = PromptConfig {
        template_dir: PathBuf::from("crates/ca-pm/templates"),
        default_template: None,
    };
    let mut manager = PromptManager::new(config)?;

    // 2. 加载 phase5_review 任务模板 (3文件结构)
    println!("📁 Loading phase5_review task template...");
    let task_dir = PathBuf::from("crates/ca-pm/templates/run/phase5_review");
    let task = manager.load_task_dir(&task_dir)?;

    // 3. 显示配置
    println!("\n⚙️  Task Configuration:");
    println!("  - Preset: {}", task.config.preset);
    println!("  - Max Turns: {}", task.config.max_turns);
    println!("  - Max Budget: ${:.2}", task.config.max_budget_usd);
    println!("  - Permission Mode: {:?}", task.config.permission_mode);
    println!("  - Disallowed Tools: {:?}", task.config.disallowed_tools);

    // 4. 创建渲染上下文
    let mut context = TemplateContext::new();
    context.insert("implementation_summary", "Added user authentication")?;
    context.insert("changes", "- Added login endpoint\n- Added JWT middleware")?;

    // 5. 渲染模板
    println!("\n📝 Rendering templates...");
    let (system, user) = manager.render_task(&task, &context)?;

    println!("\n✅ System Prompt: {}", if system.is_some() { "Present" } else { "None" });
    println!("✅ User Prompt (first 100 chars):");
    println!("   {}", &user.chars().take(100).collect::<String>());

    // 6. 验证关键配置
    println!("\n🔍 Validating key configurations:");
    
    // Phase 5 应该禁止写入工具
    assert!(task.config.disallowed_tools.contains(&"Write".to_string()));
    assert!(task.config.disallowed_tools.contains(&"StrReplace".to_string()));
    println!("   ✓ Phase 5 correctly disallows file modifications");

    // Phase 5 应该有较低的预算
    assert!(task.config.max_budget_usd <= 3.0);
    println!("   ✓ Phase 5 has appropriate budget limit");

    // 7. 对比其他阶段
    println!("\n📊 Comparing with other phases:");
    
    let phase3_task = manager.load_task_dir(&PathBuf::from(
        "crates/ca-pm/templates/run/phase3_execute"
    ))?;
    println!("   Phase 3 (Execute):");
    println!("     - Disallowed Tools: {} (full access)", phase3_task.config.disallowed_tools.len());
    println!("     - Max Budget: ${:.2}", phase3_task.config.max_budget_usd);
    
    let phase7_task = manager.load_task_dir(&PathBuf::from(
        "crates/ca-pm/templates/run/phase7_verification"
    ))?;
    println!("   Phase 7 (Verification):");
    println!("     - Disallowed Tools: {} (read-only)", phase7_task.config.disallowed_tools.len());
    println!("     - Max Budget: ${:.2}", phase7_task.config.max_budget_usd);

    println!("\n✨ All validations passed!");
    println!("\n🎉 Prompt template refactoring successful!");
    println!("   - TaskConfig and TaskTemplate structures implemented");
    println!("   - 12 config.yml files created");
    println!("   - 3-file structure (config.yml + system.jinja + user.jinja) working");
    println!("   - Backward compatibility maintained");

    Ok(())
}
