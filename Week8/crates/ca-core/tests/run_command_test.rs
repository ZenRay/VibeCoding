//! Run 命令集成测试

use ca_core::{KeywordMatcher, Phase};
use ca_pm::{PermissionMode, TaskConfig};

/// 测试 KeywordMatcher 与 Review Phase 集成
#[test]
fn test_keyword_matcher_for_review() {
    let matcher = KeywordMatcher::for_review();

    let approved_output = "After reviewing: APPROVED";
    let needs_changes_output = "Issues found: NEEDS_CHANGES";

    assert_eq!(matcher.check(approved_output), Some(true));
    assert_eq!(matcher.check(needs_changes_output), Some(false));
}

/// 测试 Review/Fix 循环逻辑
#[test]
fn test_review_fix_loop_logic() {
    const MAX_FIX_ITERATIONS: usize = 3;
    let matcher = KeywordMatcher::for_review();

    let outputs = vec![
        "NEEDS_CHANGES: Fix error",
        "NEEDS_CHANGES: Add tests",
        "APPROVED: All checks passed",
    ];

    for (iteration, output) in outputs.iter().enumerate() {
        match matcher.check(output) {
            Some(true) => {
                assert!((iteration + 1) <= MAX_FIX_ITERATIONS);
                return;
            }
            Some(false) => {
                assert!((iteration + 1) < MAX_FIX_ITERATIONS);
            }
            None => {}
        }
    }
}

/// 测试 Phase 配置传递
#[test]
fn test_phase_config_construction() {
    let task_config = TaskConfig {
        preset: true,
        tools: vec![],
        disallowed_tools: vec!["Write".to_string(), "Delete".to_string()],
        permission_mode: PermissionMode::Default,
        max_turns: 10,
        max_budget_usd: 2.0,
    };

    assert_eq!(task_config.preset, true);
    assert_eq!(task_config.disallowed_tools.len(), 2);
    assert_eq!(task_config.max_turns, 10);
}

#[test]
fn test_all_phases_defined() {
    let phases = vec![
        Phase::Observer,
        Phase::Planning,
        Phase::ExecutePhase3,
        Phase::ExecutePhase4,
        Phase::Review,
        Phase::Fix,
        Phase::Verification,
    ];

    assert_eq!(phases.len(), 7);
}
