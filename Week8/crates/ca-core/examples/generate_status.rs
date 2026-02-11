//! 演示生成 status.md

use ca_core::{FeatureState, StatusDocument};

fn main() {
    // 创建示例 state
    let mut state = FeatureState::new(
        "user-auth".to_string(),
        "用户认证功能".to_string(),
        "Claude".to_string(),
        "claude-3-5-sonnet-20241022".to_string(),
    );

    // 模拟一些阶段
    use ca_core::{PhaseCost, PhaseResult, PhaseState, Status};
    use chrono::Utc;
    use std::collections::HashMap;

    state.phases.push(PhaseState {
        phase: 1,
        name: "构建 Observer".to_string(),
        status: Status::Completed,
        started_at: Some(Utc::now()),
        completed_at: Some(Utc::now()),
        duration_seconds: Some(900),
        cost: Some(PhaseCost {
            tokens_input: 2500,
            tokens_output: 1200,
            cost_usd: 0.05,
        }),
        result: Some(PhaseResult {
            success: true,
            output_file: Some("phase1-observer.md".to_string()),
            extra: HashMap::new(),
        }),
    });

    state.phases.push(PhaseState {
        phase: 2,
        name: "制定计划".to_string(),
        status: Status::Completed,
        started_at: Some(Utc::now()),
        completed_at: Some(Utc::now()),
        duration_seconds: Some(900),
        cost: Some(PhaseCost {
            tokens_input: 3500,
            tokens_output: 2100,
            cost_usd: 0.08,
        }),
        result: Some(PhaseResult {
            success: true,
            output_file: Some("phase2-plan.md".to_string()),
            extra: HashMap::new(),
        }),
    });

    state.phases.push(PhaseState {
        phase: 3,
        name: "执行实施 1".to_string(),
        status: Status::InProgress,
        started_at: Some(Utc::now()),
        completed_at: None,
        duration_seconds: None,
        cost: Some(PhaseCost {
            tokens_input: 1500,
            tokens_output: 800,
            cost_usd: 0.03,
        }),
        result: None,
    });

    // 更新成本汇总
    state.cost_summary.total_tokens_input = 7500;
    state.cost_summary.total_tokens_output = 4100;
    state.cost_summary.total_cost_usd = 0.16;
    state.cost_summary.estimated_remaining_cost_usd = 0.24;

    // 更新进度
    state.status.current_phase = 3;
    state.status.completion_percentage = 45;

    // 添加一些任务
    use ca_core::{TaskKind, TaskState};

    state.tasks.push(TaskState {
        id: "task-1".to_string(),
        kind: TaskKind::Implementation,
        description: "添加用户认证模块".to_string(),
        status: Status::Completed,
        assigned_phase: 3,
        files: vec!["src/auth.rs".to_string()],
    });

    state.tasks.push(TaskState {
        id: "task-2".to_string(),
        kind: TaskKind::Implementation,
        description: "集成 JWT 令牌管理".to_string(),
        status: Status::Completed,
        assigned_phase: 3,
        files: vec!["src/jwt.rs".to_string()],
    });

    state.tasks.push(TaskState {
        id: "task-3".to_string(),
        kind: TaskKind::Testing,
        description: "添加单元测试".to_string(),
        status: Status::InProgress,
        assigned_phase: 3,
        files: vec!["tests/test_auth.rs".to_string()],
    });

    // 添加文件修改记录
    use ca_core::FileModification;

    state.files_modified.push(FileModification {
        path: "src/auth.rs".to_string(),
        status: "added".to_string(),
        phase: 3,
        size_bytes: 1250,
        backup: None,
    });

    state.files_modified.push(FileModification {
        path: "src/jwt.rs".to_string(),
        status: "added".to_string(),
        phase: 3,
        size_bytes: 800,
        backup: None,
    });

    // Spec 内容
    let spec_content = r#"
## 概述

实现用户认证功能，支持 JWT 令牌管理和用户登录/注册流程。

## 需求

- 用户注册功能
- 用户登录功能
- JWT 令牌生成和验证
- 密码加密存储
- Session 管理

## 技术栈

- Rust
- JWT (jsonwebtoken)
- Bcrypt (密码加密)
"#;

    // 生成 status.md
    let doc = StatusDocument::from_feature_state(&state, spec_content);
    let markdown = doc.render_to_markdown();

    // 输出到控制台
    println!("{}", markdown);
}
