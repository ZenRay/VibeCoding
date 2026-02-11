use std::path::Path;

use crate::config::AppConfig;

pub async fn execute_templates(verbose: bool, config: &AppConfig) -> anyhow::Result<()> {
    println!("📚 可用的 Prompt 模板\n");

    // 列出所有模板目录
    let templates = list_template_dirs(&config.prompt.template_dir)?;

    if templates.is_empty() {
        println!("❌ 未找到模板");
        return Ok(());
    }

    // 按类别分组
    let mut init_templates = Vec::new();
    let mut plan_templates = Vec::new();
    let mut run_templates = Vec::new();

    for template in &templates {
        if template.starts_with("init/") {
            init_templates.push(template.as_str());
        } else if template.starts_with("plan/") {
            plan_templates.push(template.as_str());
        } else if template.starts_with("run/") {
            run_templates.push(template.as_str());
        }
    }

    // 显示 Init 模板
    if !init_templates.is_empty() {
        println!("🔧 Init 模板:");
        for template in &init_templates {
            println!("  • {}", template);
            if verbose {
                show_template_info(&config.prompt.template_dir, template)?;
            }
        }
        println!();
    }

    // 显示 Plan 模板
    if !plan_templates.is_empty() {
        println!("📋 Plan 模板:");
        for template in &plan_templates {
            println!("  • {}", template);
            if verbose {
                show_template_info(&config.prompt.template_dir, template)?;
            }
        }
        println!();
    }

    // 显示 Run 模板
    if !run_templates.is_empty() {
        println!("🚀 Run 模板 (7 Phases):");
        for template in &run_templates {
            println!("  • {}", template);
            if verbose {
                show_template_info(&config.prompt.template_dir, template)?;
            }
        }
        println!();
    }

    println!("总计: {} 个模板", templates.len());
    println!("📂 模板目录: {}", config.prompt.template_dir.display());

    Ok(())
}

/// 列出所有模板目录 (3 文件结构)
fn list_template_dirs(template_dir: &Path) -> anyhow::Result<Vec<String>> {
    let mut templates = Vec::new();

    // 遍历 init/, plan/, run/ 目录
    for category in &["init", "plan", "run"] {
        let category_dir = template_dir.join(category);
        if !category_dir.exists() {
            continue;
        }

        // 遍历子目录
        for entry in std::fs::read_dir(&category_dir)? {
            let entry = entry?;
            let path = entry.path();

            if path.is_dir() {
                // 检查是否有 user.jinja (必需文件)
                let user_jinja = path.join("user.jinja");
                if user_jinja.exists()
                    && let Some(name) = path.file_name()
                {
                    templates.push(format!("{}/{}", category, name.to_string_lossy()));
                }
            }
        }
    }

    // 排序
    templates.sort();

    Ok(templates)
}

/// 显示模板详细信息
fn show_template_info(template_dir: &Path, template_name: &str) -> anyhow::Result<()> {
    let template_path = template_dir.join(template_name);
    let config_path = template_path.join("config.yml");

    if config_path.exists() {
        let content = std::fs::read_to_string(&config_path)?;
        let config: serde_yaml::Value = serde_yaml::from_str(&content)?;

        let mut info = Vec::new();

        if let Some(preset) = config.get("preset")
            && let Some(preset_bool) = preset.as_bool()
        {
            info.push(format!("Preset: {}", preset_bool));
        }
        if let Some(max_turns) = config.get("max_turns")
            && let Some(turns) = max_turns.as_u64()
        {
            info.push(format!("Max Turns: {}", turns));
        }
        if let Some(budget) = config.get("max_budget_usd")
            && let Some(budget_f64) = budget.as_f64()
        {
            info.push(format!("Budget: ${}", budget_f64));
        }
        if let Some(permission_mode) = config.get("permission_mode")
            && let Some(mode_str) = permission_mode.as_str()
        {
            info.push(format!("Permission: {}", mode_str));
        }

        if !info.is_empty() {
            println!("      {}", info.join(", "));
        }
    }

    Ok(())
}
