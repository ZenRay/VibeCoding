//! Run 命令实现
//!
//! 执行功能开发的完整流程 (7 个阶段)

use std::path::{Path, PathBuf};
use std::sync::Arc;

use ca_core::{ExecutionEngine, Phase, Repository, StateManager, Status};
use ca_pm::{ContextBuilder, PromptConfig, PromptManager};

use crate::config::AppConfig;

/// 执行 run 命令
#[allow(clippy::too_many_arguments)]
pub async fn execute_run(
    feature_slug: String,
    phase: Option<u8>,
    resume: bool,
    dry_run: bool,
    skip_review: bool,
    skip_test: bool,
    repo: Option<PathBuf>,
    config: &AppConfig,
) -> anyhow::Result<()> {
    println!("🚀 执行功能开发: {}", feature_slug);
    println!();

    // 确定工作目录
    let repo_path = determine_repo_path(repo, &config.default_repo)?;
    println!("📂 工作目录: {}", repo_path.display());

    // 检查 specs 目录
    let feature_dir = find_feature_dir(&repo_path, &feature_slug)?;
    println!("📁 Specs 目录: {}", feature_dir.display());
    println!();

    // 加载状态管理
    let mut state_manager = StateManager::new(&feature_slug, &repo_path)?;

    // 检查是否需要恢复
    if resume || state_manager.can_resume() {
        println!("🔄 检测到中断的执行，准备恢复...");
        return resume_execution(
            state_manager,
            &repo_path,
            &feature_dir,
            dry_run,
            skip_review,
            skip_test,
            config,
        )
        .await;
    }

    // 创建 Repository 和 Agent
    let repository = Arc::new(Repository::new(&repo_path)?);
    let agent = create_agent(config)?;
    let engine = ExecutionEngine::new(agent, repository.clone());

    // 验证连接
    println!("🔌 验证 Agent 连接...");
    if !engine.validate().await? {
        anyhow::bail!("❌ Agent 连接验证失败");
    }
    println!("✅ 连接成功");
    println!();

    // 确定执行阶段
    let phases_to_run = if let Some(p) = phase {
        vec![p]
    } else {
        vec![1, 2, 3, 4, 5, 6, 7]
    };

    // 执行各个阶段
    for phase_num in phases_to_run {
        let phase = map_phase_number(phase_num);
        
        println!("═══════════════════════════════════════════");
        println!("Phase {}: {}", phase_num, phase.name());
        println!("═══════════════════════════════════════════");
        println!();

        // 标记阶段开始
        state_manager.start_phase_with_default_name(phase_num)?;

        // 跳过某些阶段
        if skip_review && phase_num == 5 {
            println!("⏭️  跳过代码审查");
            state_manager.update_phase_status(phase_num, Status::Completed)?;
            continue;
        }

        if skip_test && phase_num == 7 {
            println!("⏭️  跳过测试验证");
            state_manager.update_phase_status(phase_num, Status::Completed)?;
            continue;
        }

        // 执行阶段
        match execute_phase(
            &engine,
            &state_manager,
            phase,
            phase_num,
            &feature_dir,
            &repo_path,
            dry_run,
            config,
        )
        .await
        {
            Ok(success) => {
                if success {
                    state_manager.update_phase_status(phase_num, Status::Completed)?;
                    state_manager.save()?;
                    println!("✅ Phase {} 完成", phase_num);
                } else {
                    state_manager.update_phase_status(phase_num, Status::Failed)?;
                    state_manager.save()?;
                    anyhow::bail!("Phase {} 执行失败", phase_num);
                }
            }
            Err(e) => {
                state_manager.update_phase_status(phase_num, Status::Failed)?;
                state_manager.save()?;
                return Err(e);
            }
        }

        println!();
    }

    // 所有阶段完成
    println!("═══════════════════════════════════════════");
    println!("🎉 功能开发完成!");
    println!("═══════════════════════════════════════════");
    println!();

    // 生成 PR
    if !dry_run {
        println!("📋 准备创建 Pull Request...");
        match create_pull_request(&feature_slug, &feature_dir, &repo_path).await {
            Ok(pr_url) => {
                println!("✅ PR 已创建: {}", pr_url);
                
                // 更新状态
                if let Ok(pr_number) = extract_pr_number(&pr_url) {
                    state_manager.set_pr_info(pr_url.clone(), pr_number)?;
                    state_manager.save()?;
                }
            }
            Err(e) => {
                println!("⚠️  PR 创建失败: {}", e);
                println!("   你可以手动创建 PR");
            }
        }
    }

    Ok(())
}

/// 执行单个阶段
#[allow(clippy::too_many_arguments)]
async fn execute_phase(
    engine: &ExecutionEngine,
    state_manager: &StateManager,
    phase: Phase,
    phase_num: u8,
    feature_dir: &Path,
    repo_path: &Path,
    dry_run: bool,
    config: &AppConfig,
) -> anyhow::Result<bool> {
    // 标记阶段开始 (通过可变引用)
    // 注意: 这里需要重构,因为 state_manager 是不可变引用
    // 临时解决: 在外部调用 start_phase
    
    // 构建 Prompt
    let prompt = build_phase_prompt(
        phase,
        phase_num,
        feature_dir,
        repo_path,
        state_manager,
        config,
    )?;

    if dry_run {
        println!("🔍 [DRY RUN] 模拟执行 Phase {}", phase_num);
        println!("Prompt 长度: {} 字符", prompt.len());
        return Ok(true);
    }

    // 执行阶段
    println!("⚙️  执行中...");
    let result = engine.execute_phase(phase, prompt).await?;

    // 保存阶段输出
    save_phase_output(phase_num, &result.message, feature_dir)?;

    Ok(result.success)
}

/// 恢复中断的执行
async fn resume_execution(
    mut state_manager: StateManager,
    repo_path: &Path,
    feature_dir: &Path,
    dry_run: bool,
    skip_review: bool,
    skip_test: bool,
    config: &AppConfig,
) -> anyhow::Result<()> {
    let state = state_manager.state();
    let current_phase = state.status.current_phase;

    println!("📊 当前进度:");
    println!("  - 当前阶段: Phase {}", current_phase);
    println!("  - 完成百分比: {}%", state.status.completion_percentage);
    println!();

    // 生成恢复上下文
    let resume_context = state_manager.generate_resume_context();
    println!("🔄 恢复上下文:");
    println!("{}", resume_context);
    println!();

    // 创建 Agent 和 Engine
    let repository = Arc::new(Repository::new(repo_path)?);
    let agent = create_agent(config)?;
    let engine = ExecutionEngine::new(agent, repository);

    // 从当前阶段继续执行
    for phase_num in current_phase..=7 {
        let phase = map_phase_number(phase_num);

        println!("═══════════════════════════════════════════");
        println!("Phase {}: {}", phase_num, phase.name());
        println!("═══════════════════════════════════════════");
        println!();

        // 跳过逻辑
        if skip_review && phase_num == 5 {
            println!("⏭️  跳过代码审查");
            continue;
        }

        if skip_test && phase_num == 7 {
            println!("⏭️  跳过测试验证");
            continue;
        }

        // 使用恢复 Prompt
        let prompt = if phase_num == current_phase {
            build_resume_prompt(&state_manager, feature_dir, config)?
        } else {
            build_phase_prompt(
                phase,
                phase_num,
                feature_dir,
                repo_path,
                &state_manager,
                config,
            )?
        };

        if dry_run {
            println!("🔍 [DRY RUN] 模拟执行 Phase {}", phase_num);
            continue;
        }

        println!("⚙️  执行中...");
        let result = engine.execute_phase(phase, prompt).await?;

        if result.success {
            state_manager.update_phase_status(phase_num, Status::Completed)?;
            state_manager.save()?;
            println!("✅ Phase {} 完成", phase_num);
        } else {
            anyhow::bail!("Phase {} 执行失败", phase_num);
        }

        println!();
    }

    println!("🎉 恢复执行完成!");
    Ok(())
}

/// 构建阶段 Prompt
fn build_phase_prompt(
    phase: Phase,
    phase_num: u8,
    feature_dir: &Path,
    repo_path: &Path,
    state_manager: &StateManager,
    config: &AppConfig,
) -> anyhow::Result<String> {
    let prompt_config = PromptConfig {
        template_dir: config.prompt.template_dir.clone(),
        default_template: None,
    };
    let prompt_manager = PromptManager::new(prompt_config)?;

    // 读取 specs 文件
    let spec_content = read_spec_file(feature_dir, "spec.md")?;
    let design_content = read_spec_file(feature_dir, "design.md")?;
    let plan_content = read_spec_file(feature_dir, "plan.md")?;
    let tasks_content = read_spec_file(feature_dir, "tasks.md")?;

    // 构建上下文
    let mut context_builder = ContextBuilder::new()
        .add_variable("phase_number", phase_num)?
        .add_variable("feature_slug", state_manager.state().feature.slug.clone())?
        .add_variable("spec", spec_content)?
        .add_variable("design", design_content)?
        .add_variable("plan", plan_content)?
        .add_variable("tasks", tasks_content)?;

    // Phase 特定的上下文
    match phase_num {
        3 | 4 => {
            // 执行阶段需要之前的输出
            if phase_num == 4 {
                let phase3_output = read_phase_output(feature_dir, 3)?;
                context_builder = context_builder.add_variable("phase3_output", phase3_output)?;
            }
        }
        5 => {
            // 审查阶段需要代码变更
            let changes = collect_code_changes(repo_path)?;
            context_builder = context_builder.add_variable("changes", changes)?;
        }
        6 => {
            // 修复阶段需要审查结果
            let review_output = read_phase_output(feature_dir, 5)?;
            context_builder = context_builder.add_variable("review_output", review_output)?;
        }
        _ => {}
    }

    let context = context_builder.build()?;

    // 渲染模板
    let template_name = phase.template_path();
    prompt_manager
        .render(template_name, &context)
        .map_err(Into::into)
}

/// 生成恢复上下文
fn build_resume_prompt(
    state_manager: &StateManager,
    _feature_dir: &Path,
    config: &AppConfig,
) -> anyhow::Result<String> {
    let prompt_config = PromptConfig {
        template_dir: config.prompt.template_dir.clone(),
        default_template: None,
    };
    let prompt_manager = PromptManager::new(prompt_config)?;

    let resume_context_str = state_manager.generate_resume_context();
    let context = ContextBuilder::new()
        .add_variable("resume_context", resume_context_str)?
        .add_variable("current_phase", state_manager.state().status.current_phase)?
        .build()?;

    prompt_manager
        .render("run/resume", &context)
        .map_err(Into::into)
}

/// 创建 Pull Request
async fn create_pull_request(
    feature_slug: &str,
    feature_dir: &Path,
    _repo_path: &Path,
) -> anyhow::Result<String> {
    // 读取功能规格生成 PR 描述
    let spec = read_spec_file(feature_dir, "spec.md")?;
    let summary = extract_summary(&spec);

    // 生成 PR 标题
    let pr_title = format!("feat: {}", feature_slug.replace('-', " "));

    // 生成 PR 描述
    let pr_body = format!(
        r#"## Summary

{}

## Specs

See `specs/{}/` for detailed specifications.

## Checklist

- [x] Implementation complete
- [x] Tests added
- [x] Documentation updated
- [x] Code reviewed

"#,
        summary, feature_slug
    );

    // 使用 gh cli 创建 PR
    let output = tokio::process::Command::new("gh")
        .args([
            "pr",
            "create",
            "--title",
            &pr_title,
            "--body",
            &pr_body,
            "--head",
            &format!("feature/{}", feature_slug),
        ])
        .output()
        .await?;

    if output.status.success() {
        let pr_url = String::from_utf8_lossy(&output.stdout).trim().to_string();
        Ok(pr_url)
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("gh pr create failed: {}", error)
    }
}

//
// 辅助函数

fn determine_repo_path(
    repo: Option<PathBuf>,
    default_repo: &Option<PathBuf>,
) -> anyhow::Result<PathBuf> {
    if let Some(path) = repo {
        Ok(path)
    } else if let Some(default) = default_repo {
        Ok(default.clone())
    } else {
        std::env::current_dir().map_err(Into::into)
    }
}

fn find_feature_dir(repo_path: &Path, feature_slug: &str) -> anyhow::Result<PathBuf> {
    let specs_dir = repo_path.join("specs");
    
    // 查找匹配的目录
    for entry in std::fs::read_dir(&specs_dir)? {
        let entry = entry?;
        let path = entry.path();
        
        if path.is_dir() && let Some(name) = path.file_name().and_then(|n| n.to_str())
            && name.ends_with(feature_slug) {
            return Ok(path);
        }
    }
    
    anyhow::bail!("功能目录未找到: {}", feature_slug)
}

fn map_phase_number(phase_num: u8) -> Phase {
    match phase_num {
        1 => Phase::Observer,
        2 => Phase::Planning,
        3 => Phase::ExecutePhase3,
        4 => Phase::ExecutePhase4,
        5 => Phase::Review,
        6 => Phase::Fix,
        7 => Phase::Verification,
        _ => Phase::ExecutePhase3,
    }
}

fn read_spec_file(feature_dir: &Path, filename: &str) -> anyhow::Result<String> {
    let path = feature_dir.join(filename);
    if path.exists() {
        std::fs::read_to_string(path).map_err(Into::into)
    } else {
        Ok(String::new())
    }
}

fn read_phase_output(feature_dir: &Path, phase_num: u8) -> anyhow::Result<String> {
    let filename = format!("phase{}_output.md", phase_num);
    read_spec_file(&feature_dir.join(".ca-state"), &filename)
}

fn save_phase_output(phase_num: u8, output: &str, feature_dir: &Path) -> anyhow::Result<()> {
    let state_dir = feature_dir.join(".ca-state");
    std::fs::create_dir_all(&state_dir)?;
    
    let filename = format!("phase{}_output.md", phase_num);
    let path = state_dir.join(filename);
    
    std::fs::write(path, output)?;
    Ok(())
}

fn collect_code_changes(_repo_path: &Path) -> anyhow::Result<String> {
    // 使用 git diff 收集变更
    let output = std::process::Command::new("git")
        .args(["diff", "--cached"])
        .output()?;
    
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

fn extract_summary(spec: &str) -> String {
    // 提取规格中的概述部分
    spec.lines()
        .skip_while(|line| !line.starts_with("## Overview") && !line.starts_with("## 概述"))
        .skip(1)
        .take_while(|line| !line.starts_with("##"))
        .collect::<Vec<_>>()
        .join("\n")
        .trim()
        .to_string()
}

fn extract_pr_number(pr_url: &str) -> anyhow::Result<u32> {
    // 从 PR URL 中提取编号
    // 例如: https://github.com/user/repo/pull/123
    pr_url
        .split('/')
        .next_back()
        .and_then(|s| s.parse().ok())
        .ok_or_else(|| anyhow::anyhow!("无法从 PR URL 提取编号"))
}

fn create_agent(config: &AppConfig) -> anyhow::Result<Arc<dyn ca_core::Agent>> {
    use ca_core::{AgentConfig, AgentFactory, AgentType};

    let agent_type = match config.agent.agent_type.as_str() {
        "claude" => AgentType::Claude,
        "cursor" => AgentType::Cursor,
        "copilot" => AgentType::Copilot,
        _ => anyhow::bail!("不支持的 Agent 类型: {}", config.agent.agent_type),
    };

    let agent_config = AgentConfig {
        agent_type,
        api_key: config.agent.api_key.clone(),
        model: Some(config.agent.model.clone()),
        api_url: config.agent.api_url.clone(),
    };

    AgentFactory::create(agent_config).map_err(Into::into)
}
