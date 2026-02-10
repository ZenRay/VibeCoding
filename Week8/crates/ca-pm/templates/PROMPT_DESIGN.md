# Prompt Template Design: System vs User Prompts

## Overview

This document clarifies which prompts are **system prompts** (agent configuration) and which are **user prompts** (task-specific instructions).

## Design Philosophy

**Convention over Configuration**: 
- Minimize variables that can be derived from context
- Use sensible defaults
- Only expose variables that genuinely vary between executions

**Context-Driven**:
- ExecutionEngine provides most context automatically
- StateManager tracks execution state
- Repository provides codebase information

---

## Prompt Classification

### System Prompts (Agent Configuration)

System prompts define the agent's role, capabilities, and behavior guidelines. These are set once per agent type and rarely change.

#### 1. Agent Role Definition (sys_agent_role.jinja)

**Purpose**: Define what the agent is and its core capabilities.

**Content**:
```jinja
You are an expert software engineering agent capable of:
- Analyzing codebases and understanding architectural patterns
- Planning and implementing features with best practices
- Writing production-quality code with tests
- Performing code reviews and suggesting improvements
- Creating comprehensive documentation

Your responses should be:
- Precise and actionable
- Well-structured with clear sections
- Focused on maintainability and quality
- Following industry best practices
```

**Agent-Specific Variations**:
- **Claude**: Emphasize structured thinking, step-by-step reasoning
- **Copilot**: Emphasize code completion, inline suggestions
- **Cursor**: Emphasize IDE integration, context awareness

**Variables**: None (static text)

#### 2. Output Format Guidelines (sys_output_format.jinja)

**Purpose**: Define expected output structure.

**Content**:
```jinja
## Output Format Requirements

Always structure your responses with:

1. **Summary**: Brief overview of what was done
2. **Details**: Comprehensive explanation
3. **Code**: Complete, runnable code blocks
4. **Verification**: How to verify the changes

For code blocks, always use:
```language
<code here>
```

For file operations, specify:
- File path (relative to repo root)
- Action (create/modify/delete)
- Complete content (not diffs)
```

**Agent-Specific Variations**:
- **Claude**: Accepts markdown with nested structures
- **Copilot**: Prefers inline code suggestions
- **Cursor**: Supports file tree annotations

**Variables**: None (static text)

#### 3. Quality Standards (sys_quality.jinja)

**Purpose**: Define code quality expectations.

**Content**:
```jinja
## Code Quality Standards

Adhere to:

1. **Clean Code**: Meaningful names, single responsibility, DRY
2. **Error Handling**: Graceful failure, informative errors
3. **Testing**: Unit tests for all new functionality
4. **Documentation**: Clear comments, docstrings, README updates
5. **Security**: Input validation, no hardcoded secrets
6. **Performance**: Efficient algorithms, avoid premature optimization

Follow the language-specific conventions already present in the codebase.
```

**Agent-Specific Variations**: Minimal (universal standards)

**Variables**: None (static text)

---

### User Prompts (Task-Specific)

User prompts contain task-specific instructions and context. These change with each execution.

#### Phase-Specific Prompts

**1. phase1_observer.jinja** (User Prompt)

**Variables** (all provided by ExecutionEngine):
- `feature_spec` - Feature specification text
- `repo_path` - Repository absolute path
- `language` - Primary language (detected)
- `files[]` - List of relevant files with:
  - `path` - Relative path
  - `lines` - Line count (from metadata)
  - `size_kb` - File size (from metadata)
  - `content` - File content

**Removed Variables** (can be derived):
- ❌ `project.framework` - Can be detected from files
- ❌ `file.summary` - Not needed, agent can analyze
- ❌ `project.name` - Use repo_path basename

**2. phase2_planning.jinja** (User Prompt)

**Variables**:
- `observer_results` - Output from Phase 1
- `feature_spec` - Feature specification

**Removed Variables**:
- ❌ `constraints.time_estimate` - Not needed, agent decides
- ❌ `constraints.complexity` - Agent evaluates
- ❌ `constraints.breaking_changes` - Specify in feature_spec if relevant

**3. phase3_execute.jinja / phase4_execute.jinja** (User Prompt)

**Variables**:
- `phase_number` - 3 or 4
- `is_resume` - Boolean (from state.yml)
- `plan` - Implementation plan text
- `current_task.id` - Current task ID
- `current_task.kind` - Task kind (enum)
- `current_task.description` - Task description
- `current_task.files` - Array of file paths
- `context_files[]` - Files needed for this task:
  - `path` - File path
  - `language` - Language (detected)
  - `content` - File content
- `is_last_task_in_phase` - Boolean (computed)

**If is_resume = true**:
- `resume.checkpoint` - Last checkpoint ID
- `resume.context` - Natural language context
- `completed_tasks[]` - Array of completed tasks
- `modified_files[]` - Array of modified file paths

**Removed Variables**:
- ❌ `plan.phase_tasks` - Use `plan` (single string)
- ❌ `current_task.dependencies` - Not shown to agent, handled by engine
- ❌ `resume.last_checkpoint` - Use simpler `resume.checkpoint`
- ❌ `current_phase`, `completed_count`, `total_count` - Derived from context

**4. phase5_review.jinja** (User Prompt)

**Variables**:
- `implementation_summary` - Summary text
- `changes[]` - Array of changes:
  - `file_path` - File path
  - `type` - create/modify/delete
  - `language` - Language
  - `content` - New content
  - `explanation` - Why this change
- `tests[]` - Array of tests:
  - `file` - Test file path
  - `description` - What it tests

**Removed Variables**:
- ❌ `changes[].phase` - Not needed for review

**5. phase6_fix.jinja** (User Prompt)

**Variables**:
- `review_results` - Review output text
- `issues[]` - Array of issues:
  - `title` - Issue title
  - `severity` - critical/high/medium/low
  - `category` - Category name
  - `location` - File:line
  - `description` - Issue description
  - `recommendation` - How to fix
  - `example` - Optional code example
  - `language` - For example
- `affected_files[]` - Files with issues:
  - `path` - File path
  - `language` - Language
  - `content` - Current content

**6. phase7_verification.jinja** (User Prompt)

**Variables**:
- `implementation_summary` - Overall summary
- `all_changes[]` - All file changes:
  - `file` - File path
  - `type` - Change type
- `tests[]` - All tests:
  - `file` - Test file
  - `description` - What it tests

**7. resume.jinja** (User Prompt)

**Variables**:
- `feature_name` - Feature name
- `interruption.timestamp` - ISO timestamp
- `interruption.checkpoint` - Checkpoint ID
- `interruption.phase` - Phase number
- `interruption.task` - Task ID
- `completed_phases[]` - Completed phases:
  - `number` - Phase number
  - `name` - Phase name
  - `duration` - Duration string
  - `cost` - Cost in USD
  - `tasks_completed` - Count
  - `tasks_total` - Total
- `completed_tasks[]` - All completed tasks (simplified)
- `modified_files[]` - All modified files (simplified)
- `current_phase` - Current phase number
- `phase_progress` - Percentage
- `overall_progress` - Percentage
- `resume.context` - Natural language
- `resume.last_action` - What was being done
- `relevant_files[]` - Current file states
- `next_task` - Next task info
- `remaining_phase_tasks[]` - Remaining in phase
- `remaining_phases[]` - Remaining phases

---

## Variable Provisioning by ExecutionEngine

### Automatic Context

ExecutionEngine provides automatically:

```rust
pub struct ExecutionContext {
    // Repository info
    pub repo_path: PathBuf,
    pub language: String,  // detected
    
    // Feature info
    pub feature_name: String,
    pub feature_spec: String,
    
    // Current state (from state.yml)
    pub current_phase: u8,
    pub current_task: Task,
    pub is_resume: bool,
    
    // Phase results
    pub observer_results: Option<String>,
    pub plan: Option<String>,
    pub implementation_summary: Option<String>,
    pub review_results: Option<String>,
    
    // Files
    pub context_files: Vec<FileContext>,
    pub modified_files: Vec<PathBuf>,
    
    // Resume info
    pub resume_info: Option<ResumeInfo>,
}
```

### State-Derived Variables

From `state.yml`:
- `is_resume` - Check if state exists and status != completed
- `resume.checkpoint` - From `resume.last_checkpoint`
- `resume.context` - From `resume.resume_prompt_context`
- `completed_tasks` - From `tasks` where status = completed
- `completed_phases` - From `phases` where status = completed
- `modified_files` - From `files_modified`
- `current_phase` - From `status.current_phase`
- `phase_progress` - Computed from task counts
- `overall_progress` - From `status.completion_percentage`

### Computed Variables

- `is_last_task_in_phase` - Check if current_task is last in phase
- `language` - Detect from repo files
- `file.lines` - Count from file content
- `file.size_kb` - From filesystem
- `phase_number` - From current_phase

---

## Command-Specific Prompts

### `code-agent init`

**System Prompt**: Standard (sys_agent_role + sys_output_format + sys_quality)

**User Prompt**: `init/project_setup.jinja`

**Variables**:
- `repo_path` - Repository path (from --repo or cwd)
- `language` - Primary language (detected)

**Task**: Create project structure, update .gitignore, create README

### `code-agent plan`

**System Prompt**: Standard

**User Prompt**: `plan/feature_analysis.jinja` (to be created)

**Variables**:
- `feature_description` - User input
- `repo_path` - Repository path
- `language` - Primary language
- `existing_specs` - List of existing feature slugs

**Task**: Analyze feature and generate specs

### `code-agent run` (Each Phase)

**System Prompt**: Standard

**User Prompts**: 
- Phase 1: `run/phase1_observer.jinja`
- Phase 2: `run/phase2_planning.jinja`
- Phase 3-4: `run/phase3_execute.jinja`, `run/phase4_execute.jinja`
- Phase 5: `run/phase5_review.jinja`
- Phase 6: `run/phase6_fix.jinja`
- Phase 7: `run/phase7_verification.jinja`
- Resume: `run/resume.jinja` (if interrupted)

**Variables**: See phase-specific sections above

---

## Agent SDK Differences

### Claude Agent
**System Prompt Requirements**:
- Supports complex structured prompts
- Benefits from explicit reasoning steps
- Good with long context

**Adaptations**:
- Can include more detailed guidelines
- Use nested markdown structures
- Emphasize "think step by step"

### GitHub Copilot Agent
**System Prompt Requirements**:
- Optimized for code completion
- Prefers concise instructions
- Works best with inline context

**Adaptations**:
- Shorter system prompts
- More emphasis on code examples
- Focus on immediate next action

### Cursor Agent
**System Prompt Requirements**:
- IDE-integrated
- Aware of current file/cursor position
- Supports file tree operations

**Adaptations**:
- Include IDE navigation hints
- Reference current file/position
- Support multi-file edits

### Unified Approach

For initial implementation:
- Use Claude-optimized prompts (most detailed)
- Test with Claude Agent first
- Adapt for other agents as needed

**Shared system prompts**:
- `sys_agent_role.jinja` - Base role definition
- `sys_output_format.jinja` - Output structure
- `sys_quality.jinja` - Quality standards

**Agent-specific overrides**:
- `sys_agent_role_claude.jinja` - Claude-specific additions
- `sys_agent_role_copilot.jinja` - Copilot-specific additions
- `sys_agent_role_cursor.jinja` - Cursor-specific additions

---

## Summary

**System Prompts** (Set once, rarely change):
- Agent role and capabilities
- Output format requirements
- Quality standards
- Agent-specific behavior

**User Prompts** (Per task):
- Task-specific instructions
- Feature/task context
- Code context
- State information

**Variable Strategy**:
- ✅ Keep: Variables that genuinely vary per execution
- ✅ Keep: Variables provided by ExecutionEngine context
- ❌ Remove: Variables that can be derived/detected
- ❌ Remove: Variables for configuration that should be convention

**Simplified Variables** (Essential only):
- Feature info: `feature_name`, `feature_spec`
- Repo info: `repo_path`, `language`
- State: `is_resume`, `current_phase`, `current_task`
- Context: `files[]`, `context_files[]`, `plan`, `*_results`
- Resume: `resume.checkpoint`, `resume.context`, `completed_*`

---

**Version**: 1.0
**Date**: 2026-02-10
