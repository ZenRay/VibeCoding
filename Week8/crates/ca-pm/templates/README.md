# Code Agent Prompt Templates

This directory contains all prompt templates used by Code Agent to interact with various AI agents (Claude, Copilot, Cursor).

## Template Structure

```
templates/
├── init/                    # Initialization templates
│   └── project_setup.jinja
├── plan/                    # Planning phase templates
│   ├── feature_analysis.jinja
│   ├── task_breakdown.jinja
│   └── milestone_planning.jinja
├── run/                     # Execution phase templates
│   ├── phase1_observer.jinja      # Phase 1: Build Observer
│   ├── phase2_planning.jinja      # Phase 2: Create Plan
│   ├── phase3_execute.jinja       # Phase 3: Execute Implementation 1
│   ├── phase4_execute.jinja       # Phase 4: Execute Implementation 2
│   ├── phase5_review.jinja        # Phase 5: Code Review
│   ├── phase6_fix.jinja           # Phase 6: Apply Fixes
│   ├── phase7_verification.jinja  # Phase 7: Final Verification
│   └── resume.jinja               # Resume from interruption
└── common/                  # Common utility templates
    ├── code_context.jinja
    ├── file_structure.jinja
    └── task_context.jinja
```

## Template Language

All templates use **Jinja2** syntax with MiniJinja engine.

### Common Variables

#### Project Context
```jinja
{{ project.repo_path }}
{{ project.primary_language }}
{{ project.framework }}
{{ project.name }}
```

#### Feature Context
```jinja
{{ feature.name }}
{{ feature.slug }}
{{ feature.spec }}
{{ feature.description }}
```

#### Files
```jinja
{% for file in files %}
- {{ file.path }}
  Lines: {{ file.lines }}
  Size: {{ file.size_kb }} KB
  Language: {{ file.language }}
  Content: {{ file.content }}
{% endfor %}
```

#### Tasks
```jinja
{% for task in tasks %}
- ID: {{ task.id }}
  Kind: {{ task.kind }}  # implementation, refactoring, bugfix, testing, verification
  Description: {{ task.description }}
  Files: {{ task.files | join(', ') }}
  Status: {{ task.status }}
{% endfor %}
```

#### State (for resume)
```jinja
{{ resume.context }}
{{ resume.last_checkpoint }}
{{ interruption.timestamp }}
{{ interruption.phase }}
{{ interruption.task }}
```

## Usage

### Loading Templates

```rust
use ca_pm::{PromptManager, PromptConfig};

let config = PromptConfig {
    template_dir: PathBuf::from("templates"),
    default_template: "default".to_string(),
};

let mut manager = PromptManager::new(config)?;
manager.load_templates()?;
```

### Rendering Templates

```rust
use ca_pm::ContextBuilder;

let mut context = ContextBuilder::new();
context
    .add_variable("feature", &feature)?
    .add_variable("files", &files)?
    .add_variable("project", &project)?;

let prompt = manager.render("run/phase1_observer", &context.build())?;
```

### Resume Support

When resuming from interruption:

```rust
let mut context = ContextBuilder::new();
context
    .add_variable("is_resume", &true)?
    .add_variable("resume", &resume_info)?
    .add_variable("completed_tasks", &completed)?
    .add_variable("interruption", &interruption)?;

let prompt = manager.render("run/resume", &context.build())?;
```

## Template Guidelines

### Writing Prompts

1. **Be Clear and Specific**
   - Clearly state the task
   - Provide complete context
   - Define expected output format

2. **Use Structured Output**
   - Request structured responses
   - Provide examples of expected format
   - Use markdown formatting

3. **Include Guidelines**
   - Add do's and don'ts
   - Specify quality standards
   - Highlight important considerations

4. **Support Resume**
   - Check for `is_resume` flag
   - Provide resume context
   - Maintain continuity

### Variable Naming

- Use snake_case for variable names
- Use descriptive names
- Namespace related variables (e.g., `project.*`, `feature.*`)

### Conditional Sections

```jinja
{% if is_resume %}
⚠️ **RESUMING FROM INTERRUPTION**
{{ resume.context }}
{% else %}
Starting fresh execution.
{% endif %}
```

### Loops

```jinja
{% for file in files %}
- {{ file.path }} ({{ file.lines }} lines)
{% endfor %}
```

### Filters

```jinja
{{ task.files | join(', ') }}
{{ content | truncate(100) }}
```

## Phase-Specific Notes

### Phase 1: Observer
- Focus on analysis, not implementation
- Identify files, dependencies, risks
- Provide structured output for planning

### Phase 2: Planning
- Break down into atomic tasks
- Assign tasks to phases
- Estimate resources
- Include verification tasks

### Phase 3/4: Execute
- Support resume from interruption
- Track progress with state.yml
- Include code, tests, and documentation
- Handle task dependencies

### Phase 5: Review
- Comprehensive code review
- Categorize issues by severity
- Provide actionable feedback
- Include code examples

### Phase 6: Fix
- Address review issues
- Maintain code quality
- Update tests
- Verify fixes

### Phase 7: Verification
- Final quality check
- Run all tests
- Manual verification
- Deployment readiness

### Resume
- Load state from state.yml
- Provide complete context
- Continue seamlessly
- Maintain consistency

## Agent Compatibility

These templates are designed to work with:
- **Claude Agent** (claude-agent-sdk-rs)
- **GitHub Copilot Agent** (copilot-agent-sdk)
- **Cursor Agent** (cursor-agent-sdk)

All templates use standard English and structured formats that any agent can understand.

## Testing Templates

To test a template:

```bash
# Render a template with test data
cargo test template_rendering

# Validate template syntax
cargo test template_validation
```

## Contributing

When adding new templates:
1. Follow existing naming conventions
2. Use English only
3. Include comprehensive comments
4. Test with multiple agents
5. Update this README

---

**Version**: 1.0  
**Last Updated**: 2026-02-10
