"""
Validation models for query result verification.

Defines validation levels, issues, suggestions, and results for ResultValidator.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ValidationLevel(str, Enum):
    """
    Validation level for result verification.

    Attributes:
        BASIC: Local validation only (fast, no API cost).
        SEMANTIC: Includes AI semantic validation (slower, requires OpenAI).
        AUTO: Automatically choose based on result quality (smart default).
    """

    BASIC = "basic"
    SEMANTIC = "semantic"
    AUTO = "auto"


class ValidationIssue(str, Enum):
    """
    Types of validation issues detected.

    Attributes:
        EMPTY_RESULT: Query returned zero rows.
        TOO_FEW_ROWS: Result has fewer rows than expected.
        TOO_MANY_ROWS: Result has excessive rows (may need refinement).
        COLUMN_MISMATCH: Column names don't match user request keywords.
        TYPE_MISMATCH: Data types inconsistent with expectations.
        SEMANTIC_MISMATCH: AI detected semantic mismatch with user intent.
    """

    EMPTY_RESULT = "empty_result"
    TOO_FEW_ROWS = "too_few_rows"
    TOO_MANY_ROWS = "too_many_rows"
    COLUMN_MISMATCH = "column_mismatch"
    TYPE_MISMATCH = "type_mismatch"
    SEMANTIC_MISMATCH = "semantic_mismatch"


class ValidationSeverity(str, Enum):
    """
    Severity level of validation issues.

    Attributes:
        INFO: Informational, no action needed.
        WARNING: Warning, result may be suboptimal.
        ERROR: Error, result likely incorrect.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationSuggestion(BaseModel):
    """
    Suggestion for improving query results.

    Attributes:
        issue: Type of issue detected.
        severity: Severity level of the issue.
        message: Human-readable issue description.
        suggested_query: Optional improved SQL query.
        confidence: Confidence score (0.0-1.0) for the suggestion.
        reasoning: Optional AI reasoning for the suggestion.
    """

    issue: ValidationIssue
    severity: ValidationSeverity = ValidationSeverity.WARNING
    message: str
    suggested_query: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    reasoning: str | None = None


class ValidationResult(BaseModel):
    """
    Result of query result validation.

    Attributes:
        valid: Whether the result passes validation.
        issues: List of detected issues.
        suggestions: List of improvement suggestions.
        semantic_match_score: Optional AI semantic match score (0.0-1.0).
        validation_level_used: Actual validation level used.
        details: Additional validation details.
    """

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    suggestions: list[ValidationSuggestion] = Field(default_factory=list)
    semantic_match_score: float | None = Field(None, ge=0.0, le=1.0)
    validation_level_used: ValidationLevel = ValidationLevel.BASIC
    details: dict[str, object] = Field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Check if result has error-level issues."""
        return any(s.severity == ValidationSeverity.ERROR for s in self.suggestions)

    @property
    def has_warnings(self) -> bool:
        """Check if result has warning-level issues."""
        return any(s.severity == ValidationSeverity.WARNING for s in self.suggestions)


class AIValidationResponse(BaseModel):
    """
    Response from AI semantic validation.

    Attributes:
        is_relevant: Whether result semantically matches user intent.
        match_score: Semantic match score (0.0-1.0).
        reason: Explanation for the relevance assessment.
        suggestion: Optional improved SQL query.
        issues: Detected semantic issues.
    """

    is_relevant: bool
    match_score: float = Field(ge=0.0, le=1.0)
    reason: str
    suggestion: str | None = None
    issues: list[str] = Field(default_factory=list)
