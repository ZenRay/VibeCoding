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

    /// 获取 Permission Mode
    pub fn permission_mode(&self) -> &'static str {
        match self {
            // 只读阶段: Plan (相当于 ReadOnly)
            Self::Observer | Self::Planning | Self::Review | Self::Verification => "Plan",
            
            // 执行阶段: AcceptEdits (自动接受编辑)
            Self::ExecutePhase3 | Self::ExecutePhase4 | Self::Fix => "AcceptEdits",
            
            // 初始化和规划阶段: AcceptEdits
            Self::Init | Self::Plan => "AcceptEdits",
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
            let content = component.load()?;
            prompt.push_str(&content);
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
    /// 获取组件文件路径
    fn file_path(&self) -> &'static str {
        match self {
            Self::AgentRole => "system/agent_role.txt",
            Self::OutputFormat => "system/output_format.txt",
            Self::QualityStandards => "system/quality_standards.txt",
        }
    }

    /// 从文件加载组件内容
    pub fn load(&self) -> Result<String> {
        // 获取模板目录的基础路径
        // 在运行时从 ca-pm crate 的 templates 目录加载
        let template_dir = Self::get_template_dir()?;
        let file_path = template_dir.join(self.file_path());

        std::fs::read_to_string(&file_path).map_err(|e| {
            crate::error::CoreError::Config(format!(
                "Failed to load system prompt component from {}: {}",
                file_path.display(),
                e
            ))
        })
    }

    /// 获取模板目录路径
    fn get_template_dir() -> Result<std::path::PathBuf> {
        // 尝试多种方式查找模板目录
        
        // 1. 环境变量 CA_TEMPLATE_DIR
        if let Ok(template_dir) = std::env::var("CA_TEMPLATE_DIR") {
            let path = std::path::PathBuf::from(template_dir);
            if path.exists() {
                return Ok(path);
            }
        }

        // 2. 相对于当前工作目录: crates/ca-pm/templates/
        let relative_path = std::path::PathBuf::from("crates/ca-pm/templates");
        if relative_path.exists() {
            return Ok(relative_path);
        }

        // 3. 相对于可执行文件: ../share/code-agent/templates/
        if let Ok(exe_path) = std::env::current_exe()
            && let Some(parent) = exe_path.parent()
        {
            let template_path = parent.join("../share/code-agent/templates");
            if template_path.exists() {
                return Ok(template_path);
            }
        }

        // 4. 使用编译时的路径 (仅用于开发)
        let compile_time_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../ca-pm/templates");
        if compile_time_path.exists() {
            return Ok(compile_time_path);
        }

        Err(crate::error::CoreError::Config(
            "Template directory not found. Set CA_TEMPLATE_DIR environment variable.".to_string(),
        ))
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
