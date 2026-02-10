//! 集成测试
//!
//! 这些测试需要实际的 API 密钥,默认被忽略。
//! 运行方式: `cargo test --test integration_test -- --ignored`

use ca_core::{Agent, AgentRequest, ClaudeAgent};

/// 从环境变量获取 API key
fn get_api_key() -> Option<String> {
    std::env::var("ANTHROPIC_API_KEY")
        .or_else(|_| std::env::var("CLAUDE_API_KEY"))
        .ok()
}

/// 检查是否有 API key
fn has_api_key() -> bool {
    get_api_key().is_some()
}

#[tokio::test]
#[ignore = "需要 ANTHROPIC_API_KEY 环境变量"]
async fn test_claude_agent_simple_query() {
    if !has_api_key() {
        eprintln!("跳过测试: 未设置 ANTHROPIC_API_KEY");
        return;
    }

    let api_key = get_api_key().unwrap();
    let agent = ClaudeAgent::new(api_key, "claude-3-5-sonnet-20241022".to_string())
        .expect("创建 Agent 失败");

    let request = AgentRequest::new(
        "test-1".to_string(),
        "What is 2 + 2? Answer with just the number.".to_string(),
    );

    let response = agent
        .execute(request)
        .await
        .expect("Agent 执行失败");

    assert!(!response.content.is_empty(), "响应内容不应为空");
    assert!(response.content.contains('4'), "响应应包含 4");
    
    println!("响应: {}", response.content);
    println!("Token 使用: {:?}", response.tokens_used);
    println!("耗时: {}ms", response.metadata.duration_ms);
}

#[tokio::test]
#[ignore = "需要 ANTHROPIC_API_KEY 环境变量"]
async fn test_claude_agent_with_system_prompt() {
    if !has_api_key() {
        eprintln!("跳过测试: 未设置 ANTHROPIC_API_KEY");
        return;
    }

    let api_key = get_api_key().unwrap();
    let mut agent = ClaudeAgent::new(api_key, "claude-3-5-sonnet-20241022".to_string())
        .expect("创建 Agent 失败");

    // 配置系统提示词
    agent
        .configure(
            Some("You are a helpful math tutor. Always explain your reasoning.".to_string()),
            None,
            None,
            None,
        )
        .expect("配置失败");

    let request = AgentRequest::new(
        "test-2".to_string(),
        "What is 5 * 6?".to_string(),
    );

    let response = agent
        .execute(request)
        .await
        .expect("Agent 执行失败");

    assert!(!response.content.is_empty(), "响应内容不应为空");
    // 由于要求解释推理,响应应该比单纯的数字更长
    assert!(response.content.len() > 10, "响应应包含解释");
    
    println!("响应: {}", response.content);
}

#[tokio::test]
#[ignore = "需要 ANTHROPIC_API_KEY 环境变量"]
async fn test_claude_agent_validation() {
    if !has_api_key() {
        eprintln!("跳过测试: 未设置 ANTHROPIC_API_KEY");
        return;
    }

    let api_key = get_api_key().unwrap();
    let agent = ClaudeAgent::new(api_key, "claude-3-5-sonnet-20241022".to_string())
        .expect("创建 Agent 失败");

    let result = agent.validate().await;
    assert!(result.is_ok(), "验证应该成功");
    assert!(result.unwrap(), "验证应该返回 true");
}

#[tokio::test]
async fn test_claude_agent_invalid_key() {
    let agent = ClaudeAgent::new("invalid-key".to_string(), "claude-3-5-sonnet-20241022".to_string())
        .expect("创建 Agent 不应失败 (只有在执行时才验证 key)");

    // validate 应该返回 true (因为只检查 key 不为空)
    let result = agent.validate().await;
    assert!(result.is_ok());
    assert!(result.unwrap());

    // 但实际执行时应该失败
    // 注意: 这个测试会向 API 发送请求,但会因为 key 无效而失败
    // 暂时跳过,避免不必要的 API 调用
}

#[test]
fn test_agent_metadata() {
    let agent = ClaudeAgent::new(
        "test-key".to_string(),
        "claude-3-5-sonnet-20241022".to_string(),
    )
    .unwrap();

    let metadata = agent.metadata();
    assert_eq!(metadata.name, "Claude Agent");
    assert_eq!(metadata.model, "claude-3-5-sonnet-20241022");
    assert_eq!(metadata.version, "0.6.4");
    assert_eq!(metadata.limits.max_context_length, 200_000);
}

#[test]
fn test_agent_capabilities() {
    let agent = ClaudeAgent::new(
        "test-key".to_string(),
        "claude-3-5-sonnet-20241022".to_string(),
    )
    .unwrap();

    let caps = agent.capabilities();
    assert!(caps.supports_system_prompt);
    assert!(caps.supports_tool_control);
    assert!(caps.supports_permission_mode);
    assert!(caps.supports_cost_control);
    assert!(caps.supports_streaming);
    assert!(caps.supports_multimodal);
}

#[tokio::test]
#[ignore = "需要 ANTHROPIC_API_KEY 环境变量 + 预算控制测试"]
async fn test_claude_agent_with_budget() {
    if !has_api_key() {
        eprintln!("跳过测试: 未设置 ANTHROPIC_API_KEY");
        return;
    }

    let api_key = get_api_key().unwrap();
    let mut agent = ClaudeAgent::new(api_key, "claude-3-5-sonnet-20241022".to_string())
        .expect("创建 Agent 失败");

    // 配置预算限制
    agent
        .configure(
            None,
            None,
            Some(3), // 最多 3 轮
            Some(0.10), // 最多 $0.10
        )
        .expect("配置失败");

    let request = AgentRequest::new(
        "test-budget".to_string(),
        "Tell me a short joke.".to_string(),
    );

    let response = agent
        .execute(request)
        .await
        .expect("Agent 执行失败");

    assert!(!response.content.is_empty(), "响应内容不应为空");
    
    println!("响应: {}", response.content);
    println!("预算测试完成");
}
