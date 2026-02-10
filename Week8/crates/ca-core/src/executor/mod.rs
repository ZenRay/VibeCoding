use std::sync::Arc;
use serde::{Deserialize, Serialize};

use crate::agent::{Agent, AgentRequest};
use crate::repository::Repository;
use crate::error::Result;

/// 执行上下文
#[derive(Debug, Clone)]
pub struct ExecutionContext {
    /// 仓库
    pub repository: Arc<Repository>,
    
    /// 任务描述
    pub task_description: String,
    
    /// 相关文件
    pub relevant_files: Vec<String>,
}

/// 执行结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    /// 是否成功
    pub success: bool,
    
    /// 结果消息
    pub message: String,
    
    /// 修改的文件数量
    pub files_changed: usize,
    
    /// 使用的 tokens
    pub tokens_used: u32,
}

/// 执行器 - 协调 Agent 和 Repository 来完成任务
pub struct Executor {
    agent: Arc<dyn Agent>,
    repository: Arc<Repository>,
}

impl Executor {
    /// 创建新的执行器
    pub fn new(agent: Arc<dyn Agent>, repository: Arc<Repository>) -> Self {
        Self { agent, repository }
    }
    
    /// 执行任务
    pub async fn execute(&self, context: ExecutionContext) -> Result<ExecutionResult> {
        tracing::info!("Starting execution: {}", context.task_description);
        
        // 1. 读取相关文件内容
        let mut context_content = Vec::new();
        for file_path in &context.relevant_files {
            if self.repository.file_exists(file_path) {
                match self.repository.read_file(file_path) {
                    Ok(content) => {
                        context_content.push(format!("File: {}\n{}", file_path, content));
                    }
                    Err(e) => {
                        tracing::warn!("Failed to read file {}: {}", file_path, e);
                    }
                }
            }
        }
        
        // 2. 构建 Agent 请求
        let prompt = format!(
            "Task: {}\n\nContext Files:\n{}",
            context.task_description,
            context_content.join("\n\n---\n\n")
        );
        
        let request = AgentRequest {
            prompt,
            context_files: context.relevant_files.clone(),
            max_tokens: None,
            temperature: None,
        };
        
        // 3. 发送请求到 Agent
        let response = self.agent.send_request(request).await?;
        
        // 4. 应用文件修改
        let mut files_changed = 0;
        for change in &response.file_changes {
            match change.change_type {
                crate::agent::ChangeType::Create | crate::agent::ChangeType::Update => {
                    if let Some(content) = &change.content {
                        self.repository.write_file(&change.path, content)?;
                        files_changed += 1;
                        tracing::info!("Updated file: {}", change.path);
                    }
                }
                crate::agent::ChangeType::Delete => {
                    if self.repository.file_exists(&change.path) {
                        self.repository.delete_file(&change.path)?;
                        files_changed += 1;
                        tracing::info!("Deleted file: {}", change.path);
                    }
                }
            }
        }
        
        Ok(ExecutionResult {
            success: true,
            message: response.content,
            files_changed,
            tokens_used: response.tokens_used,
        })
    }
    
    /// 验证执行器是否可用
    pub async fn validate(&self) -> Result<bool> {
        self.agent.validate_connection().await
    }
}
