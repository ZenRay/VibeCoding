//! Run TUI 应用
//!
//! 4 区域布局 (Phase 列表 / 日志 / 状态栏)，非阻塞事件循环，与 RunWorker 通过 mpsc 通信。

use std::io;
use std::path::Path;
use std::time::Duration;

use ca_core::TuiEvent;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyModifiers},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use ratatui::{
    Frame, Terminal,
    backend::{Backend, CrosstermBackend},
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
};
use tokio::sync::mpsc;

use super::plan_app::{ChatMessage, ChatRole, SessionStats};

/// Phase 状态
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PhaseStatus {
    /// 未开始
    Pending,
    /// 进行中
    InProgress,
    /// 已完成
    Completed,
    /// 失败
    Failed,
}

/// Phase 进度
#[derive(Debug, Clone)]
pub struct PhaseProgress {
    pub phase_num: u8,
    pub name: String,
    pub status: PhaseStatus,
}

impl PhaseProgress {
    fn new(phase_num: u8, name: String) -> Self {
        Self {
            phase_num,
            name,
            status: PhaseStatus::Pending,
        }
    }
}

/// Run TUI 应用状态
#[allow(dead_code)]
pub struct RunApp {
    pub feature_slug: String,
    pub repo_path: String,
    pub current_phase: u8,
    pub phases: Vec<PhaseProgress>,
    pub messages: Vec<ChatMessage>,
    pub stats: SessionStats,
    pub should_quit: bool,
    pub streaming_buffer: String,
    pub scroll_offset: usize,
}

impl RunApp {
    /// 创建 RunApp
    pub fn new(feature_slug: String, repo_path: &Path) -> Self {
        let repo_path_str = repo_path.display().to_string();
        let phases = vec![
            PhaseProgress::new(1, "Observer - 项目分析".to_string()),
            PhaseProgress::new(2, "Planning - 制定计划".to_string()),
            PhaseProgress::new(3, "Execute Phase 1 - 执行实施".to_string()),
            PhaseProgress::new(4, "Execute Phase 2 - 执行实施".to_string()),
            PhaseProgress::new(5, "Review - 代码审查".to_string()),
            PhaseProgress::new(6, "Fix - 应用修复".to_string()),
            PhaseProgress::new(7, "Verification - 验证测试".to_string()),
        ];

        let mut messages = Vec::new();
        messages.push(ChatMessage {
            role: ChatRole::Assistant,
            content: format!("执行功能: {} | 工作目录: {}", feature_slug, repo_path_str),
        });
        messages.push(ChatMessage {
            role: ChatRole::Assistant,
            content: "自动执行 Phase 1-7，Ctrl+C 退出。".to_string(),
        });

        Self {
            feature_slug,
            repo_path: repo_path_str,
            current_phase: 0,
            phases,
            messages,
            stats: SessionStats::default(),
            should_quit: false,
            streaming_buffer: String::new(),
            scroll_offset: 0,
        }
    }

    /// 应用来自 Worker 的 TuiEvent
    pub fn apply_event(&mut self, event: TuiEvent) {
        match event {
            TuiEvent::StreamText(text) => {
                self.streaming_buffer.push_str(&text);
            }
            TuiEvent::ToolUse { tool, .. } => {
                self.flush_streaming();
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("🔧 调用工具: {}", tool),
                });
            }
            TuiEvent::ToolResult(result) => {
                let truncated = if result.len() > 150 {
                    format!("{}...", &result[..150])
                } else {
                    result
                };
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("   → {}", truncated),
                });
            }
            TuiEvent::Error(err) => {
                self.flush_streaming();
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("❌ 错误: {}", err),
                });
            }
            TuiEvent::Complete => {
                self.flush_streaming();
            }
            TuiEvent::StatsUpdate { turns, cost_usd } => {
                self.stats.turns = turns;
                self.stats.cost_usd = cost_usd;
            }
            TuiEvent::PhaseStart(phase_num, name) => {
                self.flush_streaming();
                self.current_phase = phase_num;
                if let Some(p) = self.phases.iter_mut().find(|p| p.phase_num == phase_num) {
                    p.status = PhaseStatus::InProgress;
                    p.name = name.clone();
                }
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("[Phase {}] 开始: {}", phase_num, name),
                });
            }
            TuiEvent::PhaseComplete(phase_num) => {
                if let Some(p) = self.phases.iter_mut().find(|p| p.phase_num == phase_num) {
                    p.status = PhaseStatus::Completed;
                }
            }
            TuiEvent::PhaseFailed(phase_num, err) => {
                if let Some(p) = self.phases.iter_mut().find(|p| p.phase_num == phase_num) {
                    p.status = PhaseStatus::Failed;
                }
                self.flush_streaming();
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("❌ Phase {} 失败: {}", phase_num, err),
                });
            }
        }
    }

    fn flush_streaming(&mut self) {
        if !self.streaming_buffer.is_empty() {
            self.messages.push(ChatMessage {
                role: ChatRole::Assistant,
                content: std::mem::take(&mut self.streaming_buffer),
            });
        }
    }
}

/// 在阻塞线程中运行 Run TUI 主循环
pub fn run_run_tui_blocking(
    mut event_rx: mpsc::Receiver<TuiEvent>,
    feature_slug: String,
    repo_path: &Path,
) -> anyhow::Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut app = RunApp::new(feature_slug, repo_path);
    let res = run_run_tui_loop(&mut terminal, &mut app, &mut event_rx);

    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    res
}

fn run_run_tui_loop<B: Backend>(
    terminal: &mut Terminal<B>,
    app: &mut RunApp,
    event_rx: &mut mpsc::Receiver<TuiEvent>,
) -> anyhow::Result<()> {
    loop {
        // 非阻塞收取 Worker 事件
        while let Ok(ev) = event_rx.try_recv() {
            app.apply_event(ev);
        }

        terminal
            .draw(|f| render_run_ui(f, app))
            .map_err(|e| anyhow::anyhow!("Terminal draw: {}", e))?;

        if app.should_quit {
            return Ok(());
        }

        if event::poll(Duration::from_millis(100))?
            && let Event::Key(key) = event::read()?
        {
            match key.code {
                KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    app.should_quit = true;
                }
                KeyCode::Esc => {
                    app.should_quit = true;
                }
                _ => {}
            }
        }
    }
}

fn render_run_ui(f: &mut Frame, app: &RunApp) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(2),
            Constraint::Min(10),
            Constraint::Length(1),
        ])
        .split(f.area());

    let title = Paragraph::new(format!(
        "Code Agent Run: {}  [Ctrl+C] 退出",
        app.feature_slug
    ))
    .style(
        Style::default()
            .fg(Color::Cyan)
            .add_modifier(Modifier::BOLD),
    )
    .alignment(Alignment::Center)
    .block(Block::default().borders(Borders::ALL));
    f.render_widget(title, chunks[0]);

    // 中间区域: 左右分栏 (Phase 列表 | 日志)
    let inner_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Length(35), Constraint::Min(20)])
        .split(chunks[1]);

    // 左侧: Phase 进度列表
    let mut phase_items: Vec<ListItem> = Vec::new();
    for p in &app.phases {
        let (prefix, style) = match p.status {
            PhaseStatus::Pending => ("[ ] ", Style::default().fg(Color::DarkGray)),
            PhaseStatus::InProgress => ("[▶] ", Style::default().fg(Color::Yellow)),
            PhaseStatus::Completed => ("[✓] ", Style::default().fg(Color::Green)),
            PhaseStatus::Failed => ("[✗] ", Style::default().fg(Color::Red)),
        };
        let line = Line::from(vec![
            Span::styled(prefix, style.add_modifier(Modifier::BOLD)),
            Span::styled(
                format!("Phase {}: {}", p.phase_num, p.name),
                Style::default().fg(Color::White),
            ),
        ]);
        phase_items.push(ListItem::new(line));
    }
    let phase_list =
        List::new(phase_items).block(Block::default().borders(Borders::ALL).title("Phase 进度"));
    f.render_widget(phase_list, inner_chunks[0]);

    // 右侧: 日志消息
    let mut log_lines: Vec<Line> = Vec::new();
    for msg in &app.messages {
        let (prefix, style) = match msg.role {
            ChatRole::User => ("You: ", Style::default().fg(Color::Green)),
            ChatRole::Assistant => ("", Style::default().fg(Color::Yellow)),
        };
        for line in msg.content.lines() {
            log_lines.push(Line::from(vec![
                Span::styled(prefix, style.add_modifier(Modifier::BOLD)),
                Span::raw(line),
            ]));
        }
    }
    if !app.streaming_buffer.is_empty() {
        log_lines.push(Line::from(vec![
            Span::styled("", Style::default()),
            Span::raw(format!("{}█", app.streaming_buffer)),
        ]));
    }
    let log_text = if log_lines.is_empty() {
        ratatui::text::Text::from("等待执行...")
    } else {
        ratatui::text::Text::from(log_lines)
    };
    let log_para = Paragraph::new(log_text)
        .block(Block::default().borders(Borders::ALL).title("日志"))
        .wrap(Wrap { trim: false })
        .scroll((app.scroll_offset as u16, 0));
    f.render_widget(log_para, inner_chunks[1]);

    // 底部: 状态栏
    let stats_text = format!(
        "Phase {}/7 | Turns: {} | Cost: ${:.4}",
        app.current_phase, app.stats.turns, app.stats.cost_usd
    );
    let stats = Paragraph::new(stats_text)
        .style(Style::default().fg(Color::DarkGray))
        .block(Block::default().borders(Borders::ALL).title("Stats"));
    f.render_widget(stats, chunks[2]);
}

#[cfg(test)]
mod tests {
    use super::*;
    use ca_core::TuiEvent;
    use std::path::PathBuf;

    #[test]
    fn test_should_create_run_app() {
        let repo_path = PathBuf::from("/tmp/test-repo");
        let app = RunApp::new("add-user-auth".to_string(), &repo_path);

        assert_eq!(app.feature_slug, "add-user-auth");
        assert_eq!(app.repo_path, "/tmp/test-repo");
        assert_eq!(app.current_phase, 0);
        assert_eq!(app.phases.len(), 7);
        assert_eq!(app.phases[0].phase_num, 1);
        assert_eq!(app.phases[0].status, PhaseStatus::Pending);
        assert!(!app.should_quit);
        assert_eq!(app.messages.len(), 2);
    }

    #[test]
    fn test_should_apply_phase_start_event() {
        let repo_path = PathBuf::from("/tmp/test");
        let mut app = RunApp::new("test-feature".to_string(), &repo_path);

        app.apply_event(TuiEvent::PhaseStart(3, "Execute Phase 1".to_string()));

        assert_eq!(app.current_phase, 3);
        assert_eq!(app.phases[2].status, PhaseStatus::InProgress);
        assert_eq!(app.phases[2].name, "Execute Phase 1");
        assert!(app.messages.iter().any(|m| m.content.contains("[Phase 3]")));
    }

    #[test]
    fn test_should_apply_phase_complete_event() {
        let repo_path = PathBuf::from("/tmp/test");
        let mut app = RunApp::new("test-feature".to_string(), &repo_path);

        app.apply_event(TuiEvent::PhaseStart(1, "Observer".to_string()));
        app.apply_event(TuiEvent::PhaseComplete(1));

        assert_eq!(app.phases[0].status, PhaseStatus::Completed);
    }

    #[test]
    fn test_should_apply_phase_failed_event() {
        let repo_path = PathBuf::from("/tmp/test");
        let mut app = RunApp::new("test-feature".to_string(), &repo_path);

        app.apply_event(TuiEvent::PhaseStart(2, "Planning".to_string()));
        app.apply_event(TuiEvent::PhaseFailed(2, "Connection error".to_string()));

        assert_eq!(app.phases[1].status, PhaseStatus::Failed);
        assert!(app.messages.iter().any(|m| m.content.contains("失败")));
    }

    #[test]
    fn test_should_apply_stream_text_and_stats() {
        let repo_path = PathBuf::from("/tmp/test");
        let mut app = RunApp::new("test-feature".to_string(), &repo_path);

        app.apply_event(TuiEvent::StreamText("Hello ".to_string()));
        app.apply_event(TuiEvent::StreamText("World".to_string()));
        assert_eq!(app.streaming_buffer, "Hello World");

        app.apply_event(TuiEvent::Complete);
        assert!(app.streaming_buffer.is_empty());
        assert!(app.messages.iter().any(|m| m.content == "Hello World"));

        app.apply_event(TuiEvent::StatsUpdate {
            turns: 10,
            cost_usd: 0.5,
        });
        assert_eq!(app.stats.turns, 10);
        assert!((app.stats.cost_usd - 0.5).abs() < 0.001);
    }
}
