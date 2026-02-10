//! Review 和 Verification 关键词匹配模块
//!
//! 提供了 4 种关键词匹配模式,用于检测 Agent 输出中的审查和验证结果。

/// 关键词匹配器
///
/// 支持 4 种匹配模式:
/// 1. 单独一行: 完整单词匹配 (如 "APPROVED")
/// 2. 带前缀: "Verdict: APPROVED", "Result: VERIFIED"
/// 3. 特殊格式: "[APPROVED]", "**VERIFIED**", "`FAILED`"
/// 4. 末尾匹配: 在输出的最后 100 字符内匹配
pub struct KeywordMatcher {
    success_keywords: Vec<String>,
    fail_keywords: Vec<String>,
}

impl KeywordMatcher {
    /// 创建用于 Code Review 的匹配器
    ///
    /// - 成功关键词: APPROVED
    /// - 失败关键词: NEEDS_CHANGES
    pub fn for_review() -> Self {
        Self {
            success_keywords: vec!["APPROVED".to_string()],
            fail_keywords: vec!["NEEDS_CHANGES".to_string()],
        }
    }

    /// 创建用于 Verification 的匹配器
    ///
    /// - 成功关键词: VERIFIED
    /// - 失败关键词: FAILED
    pub fn for_verification() -> Self {
        Self {
            success_keywords: vec!["VERIFIED".to_string()],
            fail_keywords: vec!["FAILED".to_string()],
        }
    }

    /// 创建自定义匹配器
    ///
    /// # 参数
    ///
    /// * `success_keywords` - 成功关键词列表
    /// * `fail_keywords` - 失败关键词列表
    pub fn new(success_keywords: Vec<String>, fail_keywords: Vec<String>) -> Self {
        Self {
            success_keywords,
            fail_keywords,
        }
    }

    /// 检查输出是否包含成功/失败关键词
    ///
    /// # 返回值
    ///
    /// - `Some(true)` - 匹配到成功关键词
    /// - `Some(false)` - 匹配到失败关键词
    /// - `None` - 未匹配到任何关键词 (不确定)
    pub fn check(&self, output: &str) -> Option<bool> {
        // 优先检查成功关键词
        for success_kw in &self.success_keywords {
            if self.contains_pattern(output, success_kw) {
                return Some(true);
            }
        }

        // 然后检查失败关键词
        for fail_kw in &self.fail_keywords {
            if self.contains_pattern(output, fail_kw) {
                return Some(false);
            }
        }

        // 未匹配到任何关键词
        None
    }

    /// 使用 4 种模式检查是否包含关键词
    fn contains_pattern(&self, output: &str, keyword: &str) -> bool {
        self.match_line(output, keyword)        // 1. 单独一行
            || self.match_prefix(output, keyword)   // 2. 带前缀
            || self.match_special(output, keyword)  // 3. 特殊格式
            || self.match_tail(output, keyword)     // 4. 末尾匹配
    }

    /// 模式 1: 完整单词匹配 (单独一行)
    ///
    /// 匹配示例:
    /// - "APPROVED"
    /// - "  VERIFIED  " (忽略空格)
    fn match_line(&self, output: &str, keyword: &str) -> bool {
        output
            .lines()
            .any(|line| line.trim().eq_ignore_ascii_case(keyword))
    }

    /// 模式 2: 带前缀格式
    ///
    /// 匹配示例:
    /// - "Verdict: APPROVED"
    /// - "Result: VERIFIED"
    /// - "Status: NEEDS_CHANGES"
    /// - "Outcome: FAILED"
    fn match_prefix(&self, output: &str, keyword: &str) -> bool {
        let prefixes = ["verdict:", "result:", "status:", "outcome:"];
        let keyword_lower = keyword.to_lowercase();

        output.lines().any(|line| {
            let line_lower = line.to_lowercase();
            prefixes.iter().any(|prefix| {
                line_lower.contains(prefix) && line_lower.contains(&keyword_lower)
            })
        })
    }

    /// 模式 3: 特殊格式
    ///
    /// 匹配示例:
    /// - "[APPROVED]"
    /// - "**VERIFIED**" (Markdown 粗体)
    /// - "`FAILED`" (Markdown 代码)
    fn match_special(&self, output: &str, keyword: &str) -> bool {
        let patterns = [
            format!("[{}]", keyword),
            format!("**{}**", keyword),
            format!("`{}`", keyword),
        ];
        patterns.iter().any(|p| output.contains(p))
    }

    /// 模式 4: 末尾匹配 (最后 100 字符内)
    ///
    /// 用于捕获在输出末尾的关键词,不区分大小写。
    fn match_tail(&self, output: &str, keyword: &str) -> bool {
        let tail = &output[output.len().saturating_sub(100)..];
        tail.to_lowercase().contains(&keyword.to_lowercase())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_review_matcher_creation() {
        let matcher = KeywordMatcher::for_review();
        assert_eq!(matcher.success_keywords, vec!["APPROVED"]);
        assert_eq!(matcher.fail_keywords, vec!["NEEDS_CHANGES"]);
    }

    #[test]
    fn test_verification_matcher_creation() {
        let matcher = KeywordMatcher::for_verification();
        assert_eq!(matcher.success_keywords, vec!["VERIFIED"]);
        assert_eq!(matcher.fail_keywords, vec!["FAILED"]);
    }

    #[test]
    fn test_custom_matcher() {
        let matcher = KeywordMatcher::new(
            vec!["SUCCESS".to_string(), "OK".to_string()],
            vec!["ERROR".to_string()],
        );
        assert_eq!(matcher.success_keywords.len(), 2);
        assert_eq!(matcher.fail_keywords.len(), 1);
    }

    #[test]
    fn test_match_line_exact() {
        let matcher = KeywordMatcher::for_review();

        // 单独一行,完整匹配
        assert_eq!(matcher.check("APPROVED"), Some(true));
        assert_eq!(matcher.check("  APPROVED  "), Some(true));
        assert_eq!(matcher.check("approved"), Some(true)); // 不区分大小写

        // 失败关键词
        assert_eq!(matcher.check("NEEDS_CHANGES"), Some(false));
        assert_eq!(matcher.check("needs_changes"), Some(false));
    }

    #[test]
    fn test_match_line_multiline() {
        let matcher = KeywordMatcher::for_review();

        let output = "代码审查结果:\n\nAPPROVED\n\n所有检查通过。";
        assert_eq!(matcher.check(output), Some(true));

        let output2 = "存在问题:\n  NEEDS_CHANGES\n请修复。";
        assert_eq!(matcher.check(output2), Some(false));
    }

    #[test]
    fn test_match_prefix() {
        let matcher = KeywordMatcher::for_review();

        assert_eq!(matcher.check("Verdict: APPROVED"), Some(true));
        assert_eq!(matcher.check("Result: APPROVED"), Some(true));
        assert_eq!(matcher.check("Status: approved"), Some(true));
        assert_eq!(matcher.check("Outcome: NEEDS_CHANGES"), Some(false));
    }

    #[test]
    fn test_match_special_formats() {
        let matcher = KeywordMatcher::for_review();

        // 方括号格式
        assert_eq!(matcher.check("[APPROVED]"), Some(true));
        assert_eq!(matcher.check("结果: [APPROVED]"), Some(true));

        // Markdown 粗体
        assert_eq!(matcher.check("**APPROVED**"), Some(true));
        assert_eq!(matcher.check("状态: **NEEDS_CHANGES**"), Some(false));

        // Markdown 代码
        assert_eq!(matcher.check("`APPROVED`"), Some(true));
        assert_eq!(matcher.check("关键词: `NEEDS_CHANGES`"), Some(false));
    }

    #[test]
    fn test_match_tail() {
        let matcher = KeywordMatcher::for_verification();

        // 在末尾 100 字符内
        let long_output = format!("{}\n\nFinal result: VERIFIED", "x".repeat(500));
        assert_eq!(matcher.check(&long_output), Some(true));

        let long_output2 = format!("{}\n\nStatus: failed", "x".repeat(500));
        assert_eq!(matcher.check(&long_output2), Some(false));
    }

    #[test]
    fn test_no_match() {
        let matcher = KeywordMatcher::for_review();

        // 不包含任何关键词
        assert_eq!(matcher.check("代码看起来不错"), None);
        assert_eq!(matcher.check(""), None);
        assert_eq!(matcher.check("APPROVE"), None); // 不完全匹配
        assert_eq!(matcher.check("NEED_CHANGE"), None);
    }

    #[test]
    fn test_priority_success_over_fail() {
        let matcher = KeywordMatcher::for_review();

        // 同时包含成功和失败关键词,成功优先
        let output = "发现问题: NEEDS_CHANGES\n\n修复后: APPROVED";
        assert_eq!(matcher.check(output), Some(true));
    }

    #[test]
    fn test_edge_cases() {
        let matcher = KeywordMatcher::for_review();

        // 空字符串
        assert_eq!(matcher.check(""), None);

        // 只有空格
        assert_eq!(matcher.check("   \n  \n  "), None);

        // 关键词作为其他单词的一部分 (不应匹配单行模式,但会匹配末尾模式)
        let output = "APPROVED_BY_ADMIN"; // 会被末尾模式匹配
        assert_eq!(matcher.check(output), Some(true));
    }

    #[test]
    fn test_verification_scenarios() {
        let matcher = KeywordMatcher::for_verification();

        // 验证通过场景
        assert_eq!(
            matcher.check("所有测试通过\n\nVERIFIED"),
            Some(true)
        );
        assert_eq!(
            matcher.check("Result: **VERIFIED** ✅"),
            Some(true)
        );

        // 验证失败场景
        assert_eq!(
            matcher.check("测试失败\n\nFAILED"),
            Some(false)
        );
        assert_eq!(
            matcher.check("Status: `FAILED`"),
            Some(false)
        );
    }

    #[test]
    fn test_case_insensitivity() {
        let matcher = KeywordMatcher::for_review();

        // 测试所有模式的大小写不敏感性
        assert_eq!(matcher.check("approved"), Some(true));
        assert_eq!(matcher.check("Approved"), Some(true));
        assert_eq!(matcher.check("verdict: Approved"), Some(true));
        
        // 特殊格式保持原样 (需要精确匹配)
        assert_eq!(matcher.check("[APPROVED]"), Some(true));
        // 注意: [approved] 不会被特殊格式匹配,但会被末尾匹配
        assert_eq!(matcher.check("[approved]"), Some(true)); // 末尾模式
    }

    #[test]
    fn test_realistic_review_output() {
        let matcher = KeywordMatcher::for_review();

        let review_approved = r#"
# Code Review Results

## Summary
All changes look good. The implementation follows best practices.

## Checks
- ✅ Code style
- ✅ Tests coverage
- ✅ Documentation

## Verdict
**APPROVED**
"#;
        assert_eq!(matcher.check(review_approved), Some(true));

        let review_needs_changes = r#"
# Code Review Results

## Issues Found
1. Missing error handling
2. Incomplete tests

## Verdict: NEEDS_CHANGES

Please address the issues above.
"#;
        assert_eq!(matcher.check(review_needs_changes), Some(false));
    }
}
