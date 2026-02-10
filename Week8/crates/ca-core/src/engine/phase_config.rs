use crate::error::Result;
use serde::{Deserialize, Serialize};

/// 执行阶段
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Phase {
    /// 初始化
    Init,
    /// 规划
    Plan,
    /// Run Phase 1: 构建 Observer
    Observer,
    /// Run Phase 2: 制定计划
    Planning,
    /// Run Phase 3: 执行实施 1
    ExecutePhase3,
    /// Run Phase 4: 执行实施 2
    ExecutePhase4,
    /// Run Phase 5: 代码审查
    Review,
    /// Run Phase 6: 应用修复
    Fix,
    /// Run Phase 7: 验证测试
    Verification,
}

impl Phase {
    /// 获取阶段编号
    pub fn number(&self) -> u8 {
        match self {
            Self::Init => 0,
            Self::Plan => 0,
            Self::Observer => 1,
            Self::Planning => 2,
            Self::ExecutePhase3 => 3,
            Self::ExecutePhase4 => 4,
            Self::Review => 5,
            Self::Fix => 6,
            Self::Verification => 7,
        }
    }

    /// 获取阶段名称
    pub fn name(&self) -> &'static str {
        match self {
            Self::Init => "Initialize Project",
            Self::Plan => "Plan Feature",
            Self::Observer => "Build Observer",
            Self::Planning => "Build Plan",
            Self::ExecutePhase3 => "Execute Phase 1",
            Self::ExecutePhase4 => "Execute Phase 2",
            Self::Review => "Code Review",
            Self::Fix => "Apply Fixes",
            Self::Verification => "Verification",
        }
    }

    /// 获取允许的工具列表
    pub fn allowed_tools(&self) -> Vec<&'static str> {
        match self {
            Self::Init => vec!["Read", "Write", "ListFiles"],
            Self::Plan => vec!["Read", "ListFiles", "Write"],
            Self::Observer => vec!["Read"],
            Self::Planning => vec![],
            Self::ExecutePhase3 | Self::ExecutePhase4 => vec!["Read", "Write", "Bash"],
            Self::Review => vec!["Read"],
            Self::Fix => vec!["Read", "Write"],
            Self::Verification => vec!["Read", "Bash"],
        }
    }

    /// 获取最大轮次
    pub fn max_turns(&self) -> usize {
        match self {
            Self::Init => 10,
            Self::Plan => 20,
            Self::Observer | Self::Planning => 5,
            Self::ExecutePhase3 | Self::ExecutePhase4 => 30,
            Self::Review | Self::Verification => 10,
            Self::Fix => 15,
        }
    }

    /// 获取最大预算 (USD)
    pub fn max_budget(&self) -> Option<f64> {
        match self {
            Self::ExecutePhase3 | Self::ExecutePhase4 => Some(5.0),
            _ => None,
        }
    }

    /// 获取模板路径
    pub fn template_path(&self) -> &'static str {
        match self {
            Self::Init => "init/project_setup",
            Self::Plan => "plan/feature_analysis",
            Self::Observer => "run/phase1_observer",
            Self::Planning => "run/phase2_planning",
            Self::ExecutePhase3 => "run/phase3_execute",
            Self::ExecutePhase4 => "run/phase4_execute",
            Self::Review => "run/phase5_review",
            Self::Fix => "run/phase6_fix",
            Self::Verification => "run/phase7_verification",
        }
    }

    /// 构建系统提示词
    pub fn build_system_prompt(&self) -> Result<String> {
        let components = self.system_prompt_components();
        let mut prompt = String::new();

        for component in components {
            prompt.push_str(component.content());
            prompt.push_str("\n\n");
        }

        Ok(prompt)
    }

    /// 获取系统提示词组件
    fn system_prompt_components(&self) -> Vec<SystemPromptComponent> {
        match self {
            Self::Init | Self::Plan => {
                vec![
                    SystemPromptComponent::AgentRole,
                    SystemPromptComponent::OutputFormat,
                ]
            }

            Self::Observer | Self::Planning | Self::Review => {
                vec![
                    SystemPromptComponent::AgentRole,
                    SystemPromptComponent::OutputFormat,
                ]
            }

            Self::ExecutePhase3 | Self::ExecutePhase4 | Self::Fix => {
                vec![
                    SystemPromptComponent::AgentRole,
                    SystemPromptComponent::OutputFormat,
                    SystemPromptComponent::QualityStandards,
                ]
            }

            Self::Verification => {
                vec![
                    SystemPromptComponent::AgentRole,
                    SystemPromptComponent::OutputFormat,
                ]
            }
        }
    }
}

/// 系统提示词组件
#[derive(Debug, Clone, Copy)]
pub enum SystemPromptComponent {
    /// Agent 角色
    AgentRole,
    /// 输出格式
    OutputFormat,
    /// 质量标准
    QualityStandards,
}

impl SystemPromptComponent {
    /// 获取组件内容
    pub fn content(&self) -> &'static str {
        match self {
            Self::AgentRole => {
                "You are an expert software engineer with deep knowledge of software architecture, \
                 design patterns, and best practices. You write clean, maintainable, and well-tested code."
            }
            Self::OutputFormat => {
                "Provide clear, structured responses. Use markdown formatting for readability. \
                 Include code examples when relevant."
            }
            Self::QualityStandards => {
                "Follow these quality standards:\n\
                 - Write clean, readable code with proper naming\n\
                 - Add appropriate comments and documentation\n\
                 - Handle errors gracefully\n\
                 - Consider edge cases and validation\n\
                 - Write tests for new functionality"
            }
        }
    }
}

/// Phase 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseConfig {
    /// 阶段
    pub phase: Phase,
    /// 系统提示词
    pub system_prompt: String,
    /// 允许的工具
    pub allowed_tools: Vec<String>,
    /// 最大轮次
    pub max_turns: usize,
    /// 最大预算
    pub max_budget: Option<f64>,
}

impl PhaseConfig {
    /// 为指定阶段创建配置
    pub fn for_phase(phase: Phase) -> Result<Self> {
        Ok(Self {
            phase,
            system_prompt: phase.build_system_prompt()?,
            allowed_tools: phase
                .allowed_tools()
                .iter()
                .map(|s| s.to_string())
                .collect(),
            max_turns: phase.max_turns(),
            max_budget: phase.max_budget(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_phase_numbers() {
        assert_eq!(Phase::Observer.number(), 1);
        assert_eq!(Phase::Planning.number(), 2);
        assert_eq!(Phase::ExecutePhase3.number(), 3);
    }

    #[test]
    fn test_phase_config() {
        let config = PhaseConfig::for_phase(Phase::Observer).unwrap();
        assert_eq!(config.phase, Phase::Observer);
        assert!(!config.system_prompt.is_empty());
        assert_eq!(config.allowed_tools, vec!["Read"]);
    }
}
