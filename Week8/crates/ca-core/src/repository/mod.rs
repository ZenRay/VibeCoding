use ignore::WalkBuilder;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

use crate::error::{CoreError, Result};

/// 文件信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileInfo {
    /// 文件路径(相对于仓库根目录)
    pub path: PathBuf,

    /// 文件大小(字节)
    pub size: u64,

    /// 是否为目录
    pub is_dir: bool,

    /// 文件扩展名
    pub extension: Option<String>,
}

/// 文件过滤器
#[derive(Debug, Clone, Default)]
pub struct FileFilter {
    /// 文件扩展名过滤
    pub extensions: Option<Vec<String>>,
    /// 文件名模式 (glob 风格)
    pub pattern: Option<String>,
    /// 最小文件大小
    pub min_size: Option<u64>,
    /// 最大文件大小
    pub max_size: Option<u64>,
    /// 是否包含隐藏文件
    pub include_hidden: bool,
}

impl FileFilter {
    /// 创建新的过滤器
    pub fn new() -> Self {
        Self::default()
    }

    /// 设置扩展名过滤
    pub fn with_extensions(mut self, extensions: Vec<String>) -> Self {
        self.extensions = Some(extensions);
        self
    }

    /// 设置文件名模式
    pub fn with_pattern(mut self, pattern: String) -> Self {
        self.pattern = Some(pattern);
        self
    }

    /// 设置大小范围
    pub fn with_size_range(mut self, min_size: Option<u64>, max_size: Option<u64>) -> Self {
        self.min_size = min_size;
        self.max_size = max_size;
        self
    }

    /// 是否包含隐藏文件
    pub fn include_hidden(mut self, include: bool) -> Self {
        self.include_hidden = include;
        self
    }

    /// 检查文件是否匹配过滤器
    pub fn matches(&self, file: &FileInfo) -> bool {
        // 跳过目录
        if file.is_dir {
            return false;
        }

        // 检查扩展名
        if let Some(ref extensions) = self.extensions {
            if let Some(ref ext) = file.extension {
                if !extensions.iter().any(|e| e == ext) {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 检查文件大小
        if let Some(min) = self.min_size
            && file.size < min
        {
            return false;
        }
        if let Some(max) = self.max_size
            && file.size > max
        {
            return false;
        }

        // 检查文件名模式
        if let Some(ref pattern) = self.pattern {
            let file_name = file.path.file_name().and_then(|n| n.to_str()).unwrap_or("");
            if !glob_match(pattern, file_name) {
                return false;
            }
        }

        true
    }
}

/// 简单的 glob 匹配实现
fn glob_match(pattern: &str, text: &str) -> bool {
    let pattern_parts: Vec<&str> = pattern.split('*').collect();

    if pattern_parts.len() == 1 {
        return text == pattern;
    }

    let mut pos = 0;
    for (i, part) in pattern_parts.iter().enumerate() {
        if i == 0 {
            // 开头部分
            if !text[pos..].starts_with(part) {
                return false;
            }
            pos += part.len();
        } else if i == pattern_parts.len() - 1 {
            // 结尾部分
            if !text[pos..].ends_with(part) {
                return false;
            }
        } else {
            // 中间部分
            if let Some(found_pos) = text[pos..].find(part) {
                pos += found_pos + part.len();
            } else {
                return false;
            }
        }
    }

    true
}

/// 仓库管理器
#[derive(Debug)]
pub struct Repository {
    /// 仓库根目录
    root: PathBuf,
}

impl Repository {
    /// 创建新的仓库管理器
    pub fn new<P: AsRef<Path>>(root: P) -> Result<Self> {
        let root = root.as_ref().to_path_buf();

        if !root.exists() {
            return Err(CoreError::Repository(format!(
                "Repository path does not exist: {}",
                root.display()
            )));
        }

        if !root.is_dir() {
            return Err(CoreError::Repository(format!(
                "Repository path is not a directory: {}",
                root.display()
            )));
        }

        Ok(Self { root })
    }

    /// 获取仓库根目录
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// 列出所有文件(遵循 .gitignore)
    pub fn list_files(&self) -> Result<Vec<FileInfo>> {
        self.list_files_with_filter(FileFilter::default())
    }

    /// 列出文件并应用过滤器
    pub fn list_files_with_filter(&self, filter: FileFilter) -> Result<Vec<FileInfo>> {
        let mut files = Vec::new();

        for entry in WalkBuilder::new(&self.root)
            .hidden(!filter.include_hidden)
            .git_ignore(true)
            .build()
        {
            let entry = entry.map_err(|e| CoreError::Repository(e.to_string()))?;
            let path = entry.path();

            if let Ok(rel_path) = path.strip_prefix(&self.root) {
                let metadata = entry
                    .metadata()
                    .map_err(|e| CoreError::Repository(e.to_string()))?;

                let file_info = FileInfo {
                    path: rel_path.to_path_buf(),
                    size: metadata.len(),
                    is_dir: metadata.is_dir(),
                    extension: path
                        .extension()
                        .and_then(|e| e.to_str())
                        .map(|s| s.to_string()),
                };

                if filter.matches(&file_info) {
                    files.push(file_info);
                }
            }
        }

        Ok(files)
    }

    /// 搜索文件
    pub fn search_files(&self, query: &str) -> Result<Vec<FileInfo>> {
        let mut results = Vec::new();
        let query_lower = query.to_lowercase();

        for file in self.list_files()? {
            if let Some(file_name) = file.path.file_name().and_then(|n| n.to_str())
                && file_name.to_lowercase().contains(&query_lower)
            {
                results.push(file);
            }
        }

        Ok(results)
    }

    /// 按扩展名过滤文件
    pub fn files_by_extension(&self, extension: &str) -> Result<Vec<FileInfo>> {
        let filter = FileFilter::new().with_extensions(vec![extension.to_string()]);
        self.list_files_with_filter(filter)
    }

    /// 读取文件内容
    pub fn read_file<P: AsRef<Path>>(&self, path: P) -> Result<String> {
        let full_path = self.root.join(path.as_ref());
        Ok(std::fs::read_to_string(full_path)?)
    }

    /// 写入文件内容
    pub fn write_file<P: AsRef<Path>>(&self, path: P, content: &str) -> Result<()> {
        let full_path = self.root.join(path.as_ref());

        // 确保父目录存在
        if let Some(parent) = full_path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        std::fs::write(full_path, content)?;
        Ok(())
    }

    /// 删除文件
    pub fn delete_file<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        let full_path = self.root.join(path.as_ref());
        std::fs::remove_file(full_path)?;
        Ok(())
    }

    /// 检查文件是否存在
    pub fn file_exists<P: AsRef<Path>>(&self, path: P) -> bool {
        self.root.join(path.as_ref()).exists()
    }

    /// 获取文件元数据
    pub fn file_metadata<P: AsRef<Path>>(&self, path: P) -> Result<std::fs::Metadata> {
        let full_path = self.root.join(path.as_ref());
        Ok(std::fs::metadata(full_path)?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_glob_match() {
        assert!(glob_match("*.rs", "test.rs"));
        assert!(glob_match("test_*.rs", "test_foo.rs"));
        assert!(glob_match("*test*", "my_test_file"));
        assert!(!glob_match("*.rs", "test.txt"));
    }

    #[test]
    fn test_file_filter() {
        let filter = FileFilter::new()
            .with_extensions(vec!["rs".to_string()])
            .with_size_range(Some(100), Some(10000));

        let file = FileInfo {
            path: PathBuf::from("test.rs"),
            size: 500,
            is_dir: false,
            extension: Some("rs".to_string()),
        };

        assert!(filter.matches(&file));
    }
}
