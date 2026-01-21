---
description: Perform comprehensive code review for Python and TypeScript codebases focusing on architecture, design patterns, and code quality.
handoffs:
  - label: Generate Implementation Tasks
    agent: speckit.tasks
    prompt: Create implementation tasks for the code review findings
  - label: Convert to GitHub Issues
    agent: speckit.taskstoissues
    prompt: Convert review findings to GitHub issues
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Command Overview

This command performs a deep, multi-dimensional code review of Python and TypeScript codebases, evaluating:

- **Architecture & Design**: Best practices, interface design, extensibility
- **Design Principles**: KISS, DRY, YAGNI, SOLID
- **Code Quality**: Function complexity, parameter counts, naming conventions
- **Design Patterns**: Builder pattern usage and applicability
- **Code Metrics**: Lines per function (≤150), parameters per function (≤7)

## Execution Flow

### 1. Parse Input Arguments

Parse user input to determine review scope:

```
Syntax: /codereview [OPTIONS] [PATH]

OPTIONS:
  --depth <quick|thorough|comprehensive>  Review depth (default: thorough)
  --focus <architecture|quality|security|all>  Focus area (default: all)
  --output <console|markdown|json>  Output format (default: markdown)
  --python-only  Review only Python files
  --typescript-only  Review only TypeScript files

PATH:
  Specific file or directory path (default: current directory)

Examples:
  /codereview
  /codereview --depth comprehensive src/
  /codereview --focus architecture --python-only
  /codereview --output json src/services/payment.ts
```

**Argument Processing**:
- Extract depth level (default: thorough)
- Extract focus area (default: all)
- Extract output format (default: markdown)
- Extract language filter (default: both Python and TypeScript)
- Extract target path (default: current working directory)

### 2. Discover Target Files

**Action**: Identify all Python and TypeScript files in scope.

**For Python**:
```bash
# Find all .py files (excluding common ignore patterns)
find <PATH> -type f -name "*.py" \
  ! -path "*/venv/*" \
  ! -path "*/.venv/*" \
  ! -path "*/node_modules/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/.pytest_cache/*"
```

**For TypeScript**:
```bash
# Find all .ts and .tsx files (excluding common ignore patterns)
find <PATH> -type f \( -name "*.ts" -o -name "*.tsx" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/.next/*" \
  ! -path "*/.cache/*" \
  ! -name "*.d.ts"
```

**Output**: List of files to review, grouped by language.

**Prioritization**:
- If depth is "quick": Review only files changed in last 5 commits
- If depth is "thorough": Review all application code (exclude tests unless significant)
- If depth is "comprehensive": Review all code including tests and configuration

### 3. Create Review Report Structure

**Action**: Initialize review report file.

**Report Path**: `./code-review-report-[TIMESTAMP].md` or specified output path.

**Report Structure**:

```markdown
# Code Review Report: [PROJECT_NAME]

**Generated**: [DATE_TIME]
**Scope**: [PATH]
**Depth**: [DEPTH_LEVEL]
**Focus**: [FOCUS_AREA]
**Files Reviewed**: [COUNT]
**Languages**: [Python/TypeScript/Both]

---

## Executive Summary

[High-level overview of findings - to be filled during review]

### Overall Health Score: [X]/100

- Architecture & Design: [X]/25
- Code Quality: [X]/25
- Maintainability: [X]/25
- Best Practices: [X]/25

### Critical Issues: [COUNT]
### High Priority Issues: [COUNT]
### Medium Priority Issues: [COUNT]
### Low Priority Issues: [COUNT]

---

## Table of Contents

1. [Architecture & Design Analysis](#architecture--design-analysis)
2. [Code Quality Assessment](#code-quality-assessment)
3. [Design Principles Compliance](#design-principles-compliance)
4. [Design Patterns Review](#design-patterns-review)
5. [Metrics & Violations](#metrics--violations)
6. [Detailed Findings by File](#detailed-findings-by-file)
7. [Recommendations & Action Items](#recommendations--action-items)
8. [Positive Highlights](#positive-highlights)

---

## 1. Architecture & Design Analysis

### 1.1 Project Structure

[Analyze directory structure and organization]

### 1.2 Separation of Concerns

[Evaluate module boundaries and responsibilities]

### 1.3 Interface Design

[Review public APIs and contracts]

### 1.4 Dependency Management

[Analyze coupling and dependencies]

### 1.5 Extensibility & Scalability

[Assess future-proofing and growth potential]

---

## 2. Code Quality Assessment

### 2.1 Naming Conventions

[Review variable, function, class naming]

### 2.2 Function Complexity

[Identify overly complex functions]

### 2.3 Code Duplication

[Find DRY violations]

### 2.4 Error Handling

[Review exception handling patterns]

### 2.5 Type Safety

[TypeScript type usage, Python type hints]

---

## 3. Design Principles Compliance

### 3.1 KISS Principle

[Keep It Simple, Stupid - identify over-engineering]

### 3.2 DRY Principle

[Don't Repeat Yourself - find repetition]

### 3.3 YAGNI Principle

[You Aren't Gonna Need It - find unnecessary abstractions]

### 3.4 SOLID Principles

#### Single Responsibility Principle
[Review SRP compliance]

#### Open/Closed Principle
[Review OCP compliance]

#### Liskov Substitution Principle
[Review LSP compliance]

#### Interface Segregation Principle
[Review ISP compliance]

#### Dependency Inversion Principle
[Review DIP compliance]

---

## 4. Design Patterns Review

### 4.1 Builder Pattern Usage

[Identify where Builder pattern is used well]
[Identify where Builder pattern should be used]

### 4.2 Other Patterns

[Review other design patterns present]

---

## 5. Metrics & Violations

### 5.1 Function Length Violations (>150 lines)

| File | Function | Lines | Recommendation |
|------|----------|-------|----------------|
| ... | ... | ... | ... |

### 5.2 Parameter Count Violations (>7 parameters)

| File | Function | Parameters | Recommendation |
|------|----------|------------|----------------|
| ... | ... | ... | ... |

### 5.3 Cyclomatic Complexity

[Functions with high complexity scores]

### 5.4 Code Coverage

[Test coverage analysis if available]

---

## 6. Detailed Findings by File

[For each file reviewed, provide structured analysis]

---

## 7. Recommendations & Action Items

### Priority 1: Critical (Fix Immediately)

- [ ] [Issue description with file:line reference]

### Priority 2: High (Fix This Sprint)

- [ ] [Issue description with file:line reference]

### Priority 3: Medium (Fix Next Sprint)

- [ ] [Issue description with file:line reference]

### Priority 4: Low (Technical Debt)

- [ ] [Issue description with file:line reference]

---

## 8. Positive Highlights

[Acknowledge well-written code and good practices]

---

## Appendix

### Review Criteria

[Document the specific criteria used for this review]

### Tools & Methods

[List tools and approaches used]
```

### 4. Perform Architecture & Design Analysis

For each file/module, evaluate:

#### 4.1 Python Architecture Best Practices

**Check for**:
- Proper package structure (`__init__.py` usage)
- Clear module boundaries and single responsibility
- Use of abstract base classes (ABC) for interfaces
- Protocol usage (Python 3.8+) for structural subtyping
- Dependency injection patterns
- Configuration management (environment variables, config files)
- Proper use of `__all__` for public API definition

**Language-Specific Patterns**:
- Factory pattern for object creation
- Context managers for resource management
- Decorators for cross-cutting concerns
- Generators for memory-efficient iteration
- Dataclasses or Pydantic models for data structures
- Type hints with mypy compliance

**Anti-patterns to Flag**:
- Circular imports
- Global mutable state
- God objects (classes doing too much)
- Tight coupling between modules
- Missing or poor error handling
- Bare `except:` clauses
- Mutable default arguments

#### 4.2 TypeScript Architecture Best Practices

**Check for**:
- Proper module organization (index.ts exports)
- Clear separation of types, interfaces, and implementations
- Use of interfaces for contracts
- Type-only imports (`import type`)
- Barrel exports for clean public APIs
- Strict TypeScript configuration usage
- Proper generic usage

**Language-Specific Patterns**:
- Factory pattern with type inference
- Builder pattern for complex object construction
- Strategy pattern with discriminated unions
- Repository pattern for data access
- Dependency injection (constructor injection)
- Immutability patterns (readonly, as const)

**Anti-patterns to Flag**:
- `any` type usage (should be minimal)
- Non-null assertion operator (`!`) overuse
- Type assertions (`as`) instead of type guards
- Missing interface for public APIs
- Inconsistent naming conventions
- Deep nesting (>3 levels)
- Large barrel files

#### 4.3 Interface Design Review

**For each public interface/class/function**:

1. **Cohesion**: Does it have a single, clear purpose?
2. **Coupling**: Are dependencies minimal and explicit?
3. **Abstraction**: Appropriate level of abstraction?
4. **Naming**: Self-documenting and intention-revealing?
5. **Contract**: Clear preconditions and postconditions?
6. **Extensibility**: Can it be extended without modification?

**Document**:
```markdown
### Interface: [Name] ([File:Line])

**Purpose**: [What it does]
**Cohesion**: ✓/✗ [Assessment]
**Coupling**: ✓/✗ [Assessment]
**Abstraction**: ✓/✗ [Assessment]
**Issues**: [List specific problems]
**Recommendation**: [Concrete improvement]
```

#### 4.4 Extensibility Assessment

**Evaluate**:
- Can new features be added without modifying existing code?
- Are there appropriate extension points?
- Is configuration externalized?
- Are hard-coded values minimized?
- Can components be easily substituted?

**Rate**: Low / Medium / High extensibility

### 5. Perform Code Quality Analysis

For each file, check:

#### 5.1 Function-Level Analysis

For each function/method:

```python
# Pseudocode for analysis
for function in file.functions:
    line_count = function.end_line - function.start_line
    param_count = len(function.parameters)
    complexity = calculate_cyclomatic_complexity(function)

    # Check metrics
    if line_count > 150:
        issues.append({
            "file": file.path,
            "function": function.name,
            "line": function.start_line,
            "severity": "high",
            "category": "function_length",
            "message": f"Function has {line_count} lines (max: 150)",
            "recommendation": "Extract smaller functions or refactor into a class"
        })

    if param_count > 7:
        issues.append({
            "file": file.path,
            "function": function.name,
            "line": function.start_line,
            "severity": "high",
            "category": "parameter_count",
            "message": f"Function has {param_count} parameters (max: 7)",
            "recommendation": "Use parameter object pattern or Builder pattern"
        })

    if complexity > 10:
        issues.append({
            "file": file.path,
            "function": function.name,
            "line": function.start_line,
            "severity": "medium",
            "category": "complexity",
            "message": f"Cyclomatic complexity is {complexity} (threshold: 10)",
            "recommendation": "Simplify control flow or extract complex logic"
        })
```

#### 5.2 Naming Convention Check

**Python**:
- Modules: `lowercase_with_underscores`
- Classes: `PascalCase`
- Functions/methods: `lowercase_with_underscores`
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Private members: `_leading_underscore`

**TypeScript**:
- Files: `kebab-case.ts` or `PascalCase.tsx`
- Classes/Interfaces: `PascalCase`
- Functions/methods: `camelCase`
- Constants: `UPPERCASE_WITH_UNDERSCORES` or `camelCase`
- Private members: `#privateField` or `private`

**Flag violations with severity: low**

#### 5.3 DRY Analysis

**Detect code duplication**:
1. Identify identical or nearly identical code blocks
2. Look for repeated logic patterns
3. Check for copy-pasted code with minor variations

**For Python**:
- Use AST analysis to detect structural similarity
- Check for repeated string literals
- Look for similar conditional blocks

**For TypeScript**:
- Analyze similar function signatures
- Check for repeated type definitions
- Look for duplicate validation logic

**Document duplicates**:
```markdown
### Duplication: [Description]

**Location 1**: [file:line]
**Location 2**: [file:line]
**Similarity**: [X]%
**Recommendation**: Extract to shared function/utility
```

#### 5.4 Error Handling Review

**Python**:
- Check for proper exception handling
- Verify specific exceptions are caught (not bare `except:`)
- Ensure exceptions are logged or re-raised appropriately
- Check for resource cleanup (try/finally or context managers)

**TypeScript**:
- Check for proper error handling in async code
- Verify Result/Either patterns for expected failures
- Check for error type definitions
- Ensure errors are properly propagated or transformed

### 6. Review Design Principles Compliance

#### 6.1 KISS Principle

**Flag violations**:
- Over-engineered solutions for simple problems
- Unnecessary abstraction layers
- Complex inheritance hierarchies
- Premature optimization

**Examples to flag**:
```python
# Bad: Over-engineered
class AbstractFactoryProviderFactory:
    def create_factory_provider(self):
        return FactoryProvider()

# Good: Simple
def create_service():
    return Service()
```

#### 6.2 YAGNI Principle

**Flag violations**:
- Unused code (functions, classes, parameters)
- Speculative generality (abstracting for future needs)
- Configuration for unused features
- Dead code paths

**Use**:
- Static analysis to find unused definitions
- Check for commented-out code
- Identify over-parameterized functions

#### 6.3 SOLID Principles

**Single Responsibility Principle**:
- Each class/module should have one reason to change
- Flag classes with multiple unrelated methods
- Flag modules mixing concerns (e.g., business logic + I/O)

**Open/Closed Principle**:
- Code should be open for extension, closed for modification
- Check for strategy/plugin patterns
- Flag large switch/if-elif chains that could be polymorphic

**Liskov Substitution Principle**:
- Derived classes must be substitutable for base classes
- Check for violations of base class contracts
- Flag methods that throw "not implemented" errors

**Interface Segregation Principle**:
- Clients shouldn't depend on interfaces they don't use
- Flag fat interfaces with many methods
- Check for interface implementations with empty methods

**Dependency Inversion Principle**:
- Depend on abstractions, not concretions
- Check for direct instantiation of concrete classes
- Flag missing dependency injection

### 7. Review Builder Pattern Usage

#### 7.1 Identify Current Builder Pattern Usage

**Search for Builder pattern indicators**:

**Python**:
```python
# Look for method chaining patterns
class SomeBuilder:
    def with_something(self, value):
        self.something = value
        return self

    def build(self):
        return SomeObject(self.something)
```

**TypeScript**:
```typescript
// Look for builder classes
class SomeBuilder {
    private something: string;

    withSomething(value: string): this {
        this.something = value;
        return this;
    }

    build(): SomeObject {
        return new SomeObject(this.something);
    }
}
```

#### 7.2 Identify Candidates for Builder Pattern

**Flag functions/constructors that should use Builder**:
- Constructors with >7 parameters
- Functions with many optional parameters
- Complex object initialization logic
- Objects with many configuration options

**Example recommendation**:
```markdown
### Builder Pattern Candidate: `UserService.__init__` (user_service.py:45)

**Current**:
```python
def __init__(self, db_host, db_port, db_user, db_pass, cache_host,
             cache_port, timeout, retry_count, log_level, debug_mode):
    # 10 parameters!
```

**Recommendation**: Implement Builder pattern
```python
class UserServiceBuilder:
    def __init__(self):
        self._config = UserServiceConfig()

    def with_database(self, host: str, port: int, user: str, password: str) -> 'UserServiceBuilder':
        self._config.db_host = host
        self._config.db_port = port
        self._config.db_user = user
        self._config.db_password = password
        return self

    def with_cache(self, host: str, port: int) -> 'UserServiceBuilder':
        self._config.cache_host = host
        self._config.cache_port = port
        return self

    def with_retry_config(self, timeout: int, retry_count: int) -> 'UserServiceBuilder':
        self._config.timeout = timeout
        self._config.retry_count = retry_count
        return self

    def with_logging(self, level: str, debug: bool = False) -> 'UserServiceBuilder':
        self._config.log_level = level
        self._config.debug_mode = debug
        return self

    def build(self) -> UserService:
        return UserService(self._config)

# Usage
service = (UserServiceBuilder()
    .with_database("localhost", 5432, "user", "pass")
    .with_cache("localhost", 6379)
    .with_retry_config(30, 3)
    .with_logging("INFO", debug=True)
    .build())
```

**Benefits**:
- Clearer intent with named methods
- Easier to add new configuration options
- Self-documenting code
- Immutable objects after build
```
```

### 8. Calculate Health Scores

**Scoring methodology**:

#### Architecture & Design (25 points)
- Proper structure: 0-5 points
- Clear interfaces: 0-5 points
- Low coupling: 0-5 points
- Good extensibility: 0-5 points
- Design patterns: 0-5 points

#### Code Quality (25 points)
- Naming conventions: 0-5 points
- Function size compliance: 0-5 points
- Parameter count compliance: 0-5 points
- Low duplication: 0-5 points
- Type safety: 0-5 points

#### Maintainability (25 points)
- Error handling: 0-5 points
- Test coverage: 0-5 points
- Documentation: 0-5 points
- Code clarity: 0-5 points
- Complexity: 0-5 points

#### Best Practices (25 points)
- KISS: 0-5 points
- DRY: 0-5 points
- YAGNI: 0-5 points
- SOLID: 0-10 points

**Total**: Sum of all categories (max 100)

### 9. Prioritize and Categorize Issues

**Severity Levels**:

- **Critical**: Serious design flaws, security issues, or bugs
  - Circular dependencies
  - SQL injection vulnerabilities
  - Memory leaks
  - Race conditions

- **High**: Significant violations of principles or metrics
  - Functions >150 lines
  - Parameters >7
  - High cyclomatic complexity (>15)
  - Major SOLID violations

- **Medium**: Moderate quality issues
  - Moderate duplication
  - Missing error handling
  - Poor naming
  - Moderate complexity (10-15)

- **Low**: Minor issues and style violations
  - Minor naming inconsistencies
  - Missing type hints
  - Minor duplication
  - Documentation gaps

### 10. Generate Detailed Report

**For each file reviewed**, create a section:

```markdown
### File: `[path/to/file.py]` ([Lines])

**Language**: Python/TypeScript
**Purpose**: [Brief description]
**Complexity Score**: [X]/10
**Issues Found**: [Count by severity]

#### Architecture Assessment

[Evaluation of structure, design, interfaces]

#### Code Quality

[Naming, complexity, duplication findings]

#### Issues

##### Critical
- [ ] **[Line X]**: [Issue description] → [Recommendation]

##### High
- [ ] **[Line X]**: [Issue description] → [Recommendation]

##### Medium
- [ ] **[Line X]**: [Issue description] → [Recommendation]

##### Low
- [ ] **[Line X]**: [Issue description] → [Recommendation]

#### Positive Aspects

[Acknowledge good practices in this file]

---
```

### 11. Create Actionable Recommendations

**Structure recommendations**:

```markdown
## Recommendations & Action Items

### Quick Wins (1-2 hours)

1. **[File:Line]**: [Issue]
   - **Impact**: [Why it matters]
   - **Effort**: Low
   - **Change**: [Specific code change]

### Short-term Improvements (1-2 days)

1. **[File:Line]**: [Issue]
   - **Impact**: [Why it matters]
   - **Effort**: Medium
   - **Approach**: [Strategy for fix]

### Long-term Refactoring (1-2 weeks)

1. **[Module/Package]**: [Issue]
   - **Impact**: [Why it matters]
   - **Effort**: High
   - **Strategy**: [Refactoring approach]
   - **Phases**: [Break down into steps]

### Technical Debt

[Long-term improvements that can be deferred]
```

### 12. Generate Summary and Report

**Executive Summary template**:

```markdown
## Executive Summary

This review analyzed **[N] files** (**[X] Python, [Y] TypeScript**) totaling **[Z] lines of code**.

### Overall Health: [Score]/100

The codebase demonstrates **[excellent/good/fair/poor]** code quality with **[few/some/many/significant]** areas requiring attention.

### Key Strengths

1. [Positive finding 1]
2. [Positive finding 2]
3. [Positive finding 3]

### Critical Areas for Improvement

1. **[Area 1]**: [Brief description and impact]
2. **[Area 2]**: [Brief description and impact]
3. **[Area 3]**: [Brief description and impact]

### Issue Breakdown

- Critical: [N] issues
- High: [N] issues
- Medium: [N] issues
- Low: [N] issues

### Recommended Next Steps

1. [Immediate action 1]
2. [Immediate action 2]
3. [Follow-up action]
```

### 13. Output Report

**Based on output format**:

- **console**: Print summary and top 10 issues to console
- **markdown**: Write full report to file
- **json**: Output structured JSON for tool integration

**Markdown output**:
- Save to `./code-review-report-[TIMESTAMP].md`
- Display file path to user
- Provide quick stats summary

**JSON output**:
- Save to `./code-review-report-[TIMESTAMP].json`
- Structure:
```json
{
  "metadata": {
    "timestamp": "...",
    "scope": "...",
    "files_reviewed": 0,
    "languages": []
  },
  "scores": {
    "overall": 0,
    "architecture": 0,
    "quality": 0,
    "maintainability": 0,
    "best_practices": 0
  },
  "issues": [
    {
      "file": "...",
      "line": 0,
      "severity": "...",
      "category": "...",
      "message": "...",
      "recommendation": "..."
    }
  ],
  "metrics": {
    "function_length_violations": [],
    "parameter_count_violations": [],
    "complexity_violations": []
  }
}
```

### 14. Offer Next Actions

After generating the report, present options:

```markdown
## Review Complete

Report saved to: `[PATH]`

### Next Steps

Would you like to:

1. **Generate implementation tasks** - Create a tasks.md file with prioritized fixes
2. **Create GitHub issues** - Convert findings to tracked issues
3. **Focus on specific category** - Deep dive into architecture/quality/security
4. **Review specific files** - Detailed review of flagged files
5. **Generate refactoring plan** - Strategic plan for major improvements

Please select an option or ask questions about the findings.
```

## Analysis Guidelines

### Python-Specific Checks

**Type Hints**:
```python
# Good
def process_user(user_id: int, name: str) -> User:
    ...

# Bad
def process_user(user_id, name):
    ...
```

**Context Managers**:
```python
# Good
with open("file.txt") as f:
    data = f.read()

# Bad
f = open("file.txt")
data = f.read()
f.close()  # Might not execute if exception
```

**List Comprehensions vs Loops**:
```python
# Good (for simple transformations)
squares = [x**2 for x in range(10)]

# Good (for complex logic)
results = []
for item in items:
    if complex_condition(item):
        processed = complex_processing(item)
        results.append(processed)

# Bad (complex logic in comprehension)
results = [complex_processing(item) for item in items if complex_condition(item)]  # Hard to read
```

**Dataclasses for Data Structures**:
```python
# Good
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

# Bad
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
```

### TypeScript-Specific Checks

**Type Safety**:
```typescript
// Good
interface User {
    id: number;
    name: string;
}

function getUser(id: number): User {
    // ...
}

// Bad
function getUser(id: any): any {
    // ...
}
```

**Discriminated Unions**:
```typescript
// Good
type Result<T> =
    | { success: true; data: T }
    | { success: false; error: string };

function handleResult<T>(result: Result<T>) {
    if (result.success) {
        console.log(result.data); // Type-safe
    } else {
        console.error(result.error); // Type-safe
    }
}

// Bad
interface Result<T> {
    success: boolean;
    data?: T;
    error?: string;
}
```

**Immutability**:
```typescript
// Good
interface Config {
    readonly host: string;
    readonly port: number;
}

const settings = {
    timeout: 30,
    retries: 3
} as const;

// Bad
interface Config {
    host: string;
    port: number;
}

const settings = {
    timeout: 30,
    retries: 3
};
```

**Proper Generic Usage**:
```typescript
// Good
function map<T, U>(items: T[], fn: (item: T) => U): U[] {
    return items.map(fn);
}

// Bad
function map(items: any[], fn: Function): any[] {
    return items.map(fn);
}
```

## Review Depth Levels

### Quick Review

**Scope**: Changed files in recent commits
**Time**: ~10 minutes
**Focus**:
- Critical issues only
- Metric violations
- Common anti-patterns

### Thorough Review (Default)

**Scope**: All application code
**Time**: ~30-60 minutes
**Focus**:
- All severity levels
- Architecture review
- Design patterns
- Code quality

### Comprehensive Review

**Scope**: All code including tests
**Time**: 1-2 hours
**Focus**:
- Deep architecture analysis
- Cross-file dependencies
- Full SOLID review
- Security analysis
- Performance considerations

## Quality Criteria

### Function Quality

A high-quality function:
- Has a single, clear purpose
- ≤150 lines
- ≤7 parameters
- Cyclomatic complexity ≤10
- Self-documenting name
- Proper error handling
- Appropriate abstraction level
- No side effects (when possible)

### Class Quality

A high-quality class:
- Single responsibility
- Clear interface
- Low coupling
- High cohesion
- Composable
- Testable
- Proper encapsulation
- No god classes

### Module Quality

A high-quality module:
- Clear purpose and scope
- Minimal dependencies
- Clean public API
- Good organization
- No circular dependencies
- Appropriate size (not too large)

## Common Patterns to Recommend

### Builder Pattern

**When to recommend**:
- >7 constructor parameters
- Many optional parameters
- Complex initialization
- Immutable objects

### Factory Pattern

**When to recommend**:
- Complex object creation logic
- Multiple object variants
- Dependency injection needed

### Strategy Pattern

**When to recommend**:
- Multiple algorithms for same task
- Large if/switch statements
- Runtime algorithm selection

### Repository Pattern

**When to recommend**:
- Data access layer
- Multiple data sources
- Testability needed for data operations

## Tools Integration

The review can leverage these tools if available:

**Python**:
- `pylint` - Static analysis
- `mypy` - Type checking
- `radon` - Complexity metrics
- `bandit` - Security issues
- `coverage` - Test coverage

**TypeScript**:
- `eslint` - Linting
- `tsc` - Type checking
- `ts-morph` - AST analysis
- `madge` - Dependency analysis

**Both**:
- `cloc` - Lines of code
- `git` - Change history
- `grep`/`ag`/`rg` - Pattern search

## Error Handling

**If no files found**:
```
ERROR: No Python or TypeScript files found in [PATH]

Please check:
1. Path is correct
2. Language filter is appropriate
3. Files are not in ignored directories
```

**If target path doesn't exist**:
```
ERROR: Path not found: [PATH]

Please provide a valid file or directory path.
```

**If no issues found**:
```
SUCCESS: Code review complete!

No issues found. The codebase follows all best practices and quality criteria.

[Still generate full report with positive highlights]
```

## Report Persistence

**Save report to**:
- `./code-review-reports/` directory (create if doesn't exist)
- Filename: `review-[TIMESTAMP]-[SCOPE].md`
- Keep last 10 reports, archive older ones

**Report metadata**:
```yaml
---
generated: 2026-01-22T10:30:00Z
scope: src/
depth: thorough
focus: all
files_reviewed: 45
languages: [Python, TypeScript]
overall_score: 78
---
```

## Final Output

Present summary and next actions:

```markdown
✅ Code Review Complete

**Report**: `./code-review-reports/review-20260122-103000-src.md`

### Summary

- **Files Reviewed**: 45 (28 Python, 17 TypeScript)
- **Overall Score**: 78/100
- **Issues Found**: 23 (2 critical, 8 high, 10 medium, 3 low)

### Top 3 Priorities

1. **[File:Line]** - [Critical issue description]
2. **[File:Line]** - [High priority issue]
3. **[File:Line]** - [High priority issue]

### Next Actions

Would you like to:
- Generate implementation tasks (`/speckit.tasks`)
- Create GitHub issues (`/speckit.taskstoissues`)
- Review specific findings in detail
- Focus on a particular category

Type your choice or ask questions about the findings.
```
