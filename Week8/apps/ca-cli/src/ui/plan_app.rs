//! Plan TUI 应用
//!
//! 3 区域布局 (Chat / Input / Stats)，非阻塞事件循环，与 PlanWorker 通过 mpsc 通信。

use std::io;
use std::path::{Path, PathBuf};
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

/// 从 TUI 发往 Worker 的消息
#[derive(Debug, Clone)]
pub enum UserMessage {
    /// 用户输入 (功能描述或后续对话)
    Input(String),
    /// 用户退出
    Quit,
}

/// 聊天消息角色
#[derive(Debug, Clone)]
pub enum ChatRole {
    User,
    Assistant,
}

/// 单条聊天消息
#[derive(Debug, Clone)]
pub struct ChatMessage {
    pub role: ChatRole,
    pub content: String,
}

/// 会话统计 (轮次、成本)
#[derive(Debug, Default, Clone)]
pub struct SessionStats {
    pub turns: u32,
    pub cost_usd: f64,
}

/// Plan TUI 应用状态
#[allow(dead_code)]
pub struct PlanApp {
    pub feature_slug: String,
    pub repo_path: String,
    pub messages: Vec<ChatMessage>,
    pub input: String,
    pub scroll_offset: usize,
    pub stats: SessionStats,
    pub should_quit: bool,
    pub input_history: Vec<String>,
    pub history_index: Option<usize>,
    /// 当前正在追加的流式内容 (Assistant)
    pub streaming_buffer: String,
    /// Agent 状态
    pub agent_status: AgentStatus,
    /// 思考动画帧计数器
    pub thinking_frame: usize,
}

/// Agent 状态
#[derive(Debug, Clone, PartialEq)]
pub enum AgentStatus {
    /// 空闲
    Idle,
    /// 思考中
    Thinking,
    /// 执行工具
    ExecutingTool(String),
    /// 完成
    Completed,
    /// 错误
    Error(String),
}

impl PlanApp {
    pub fn new(feature_slug: String, repo_path: &Path) -> Self {
        let repo_path_str = repo_path.display().to_string();
        let mut messages = Vec::new();
        
        // 检查 feature 是否已存在
        let specs_dir = repo_path.join("specs");
        let is_existing = if specs_dir.exists() {
            find_existing_feature(&specs_dir, &feature_slug).is_some()
        } else {
            false
        };
        
        // 根据是否存在显示不同的初始消息
        if is_existing {
            messages.push(ChatMessage {
                role: ChatRole::Assistant,
                content: format!(
                    "💡 Feature '{}' 已存在，将基于新的描述更新现有文档。\n\n请输入功能描述并按 Enter 发送。",
                    feature_slug
                ),
            });
        } else {
            messages.push(ChatMessage {
                role: ChatRole::Assistant,
                content: "请输入功能描述并按 Enter 发送。".to_string(),
            });
        }

        Self {
            feature_slug,
            repo_path: repo_path_str,
            messages,
            input: String::new(),
            scroll_offset: 0,
            stats: SessionStats::default(),
            should_quit: false,
            input_history: Vec::new(),
            history_index: None,
            streaming_buffer: String::new(),
            agent_status: AgentStatus::Idle,
            thinking_frame: 0,
        }
    }

    /// 应用来自 Worker 的 TuiEvent
    pub fn apply_event(&mut self, event: TuiEvent) {
        match event {
            TuiEvent::StreamText(text) => {
                self.agent_status = AgentStatus::Thinking;
                self.streaming_buffer.push_str(&text);
                self.scroll_to_bottom(); // 自动滚动
            }
            TuiEvent::ToolUse { tool, .. } => {
                self.flush_streaming();
                self.agent_status = AgentStatus::ExecutingTool(tool.clone());
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("🔧 调用工具: {}", tool),
                });
                self.scroll_to_bottom(); // 自动滚动
            }
            TuiEvent::ToolResult(result) => {
                self.agent_status = AgentStatus::Thinking;
                let truncated = if result.len() > 150 {
                    format!("{}...", &result[..150])
                } else {
                    result
                };
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("   → {}", truncated),
                });
                self.scroll_to_bottom(); // 自动滚动
            }
            TuiEvent::Error(err) => {
                self.flush_streaming();
                self.agent_status = AgentStatus::Error(err.clone());
                self.messages.push(ChatMessage {
                    role: ChatRole::Assistant,
                    content: format!("❌ 错误: {}", err),
                });
                self.scroll_to_bottom(); // 自动滚动
            }
            TuiEvent::Complete => {
                self.flush_streaming();
                self.agent_status = AgentStatus::Completed;
                self.scroll_to_bottom(); // 自动滚动
            }
            TuiEvent::StatsUpdate { turns, cost_usd } => {
                self.stats.turns = turns;
                self.stats.cost_usd = cost_usd;
            }
            TuiEvent::PhaseStart(_, _)
            | TuiEvent::PhaseComplete(_)
            | TuiEvent::PhaseFailed(_, _) => {
                // Plan TUI 不处理 Run 专用事件
            }
        }
    }
    
    /// 更新思考动画
    pub fn tick_animation(&mut self) {
        if self.agent_status == AgentStatus::Thinking {
            self.thinking_frame = (self.thinking_frame + 1) % 10;  // 10 frames for Braille spinner
        }
    }

    /// 滚动到底部
    pub fn scroll_to_bottom(&mut self) {
        self.scroll_offset = self.messages.len().saturating_sub(1);
    }

    /// 向上滚动
    pub fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(1);
    }

    /// 向下滚动
    pub fn scroll_down(&mut self) {
        let max_scroll = self.messages.len().saturating_sub(1);
        if self.scroll_offset < max_scroll {
            self.scroll_offset += 1;
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

    fn add_user_message(&mut self, content: String) {
        self.flush_streaming();
        self.messages.push(ChatMessage {
            role: ChatRole::User,
            content,
        });
        if self.messages.len() > 100 {
            self.messages.remove(0);
        }
    }

    fn send_input(&mut self, worker_tx: &mpsc::Sender<UserMessage>) {
        let text = self.input.trim().to_string();
        self.input.clear();
        if text.is_empty() {
            return;
        }
        self.add_user_message(text.clone());
        self.input_history.push(text.clone());
        let _ = worker_tx.try_send(UserMessage::Input(text));
    }
}

/// 在阻塞线程中运行 Plan TUI 主循环
pub fn run_plan_tui_blocking(
    mut event_rx: mpsc::Receiver<TuiEvent>,
    worker_tx: mpsc::Sender<UserMessage>,
    feature_slug: String,
    repo_path: &Path,
) -> anyhow::Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut app = PlanApp::new(feature_slug, repo_path);
    let res = run_plan_tui_loop(&mut terminal, &mut app, &mut event_rx, &worker_tx);

    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    res
}

fn run_plan_tui_loop<B: Backend>(
    terminal: &mut Terminal<B>,
    app: &mut PlanApp,
    event_rx: &mut mpsc::Receiver<TuiEvent>,
    worker_tx: &mpsc::Sender<UserMessage>,
) -> anyhow::Result<()> {
    loop {
        // 非阻塞收取 Worker 事件
        while let Ok(ev) = event_rx.try_recv() {
            app.apply_event(ev);
        }

        // 更新动画
        app.tick_animation();

        terminal
            .draw(|f| render_ui(f, app))
            .map_err(|e| anyhow::anyhow!("Terminal draw: {}", e))?;

        if app.should_quit {
            let _ = worker_tx.try_send(UserMessage::Quit);
            return Ok(());
        }

        // 使用更短的轮询间隔以支持动画（100ms = 10fps）
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
                KeyCode::Enter => {
                    app.send_input(worker_tx);
                    app.agent_status = AgentStatus::Thinking;
                }
                KeyCode::Up => {
                    if !app.input_history.is_empty() {
                        let idx = app.history_index.unwrap_or(app.input_history.len());
                        if idx > 0 {
                            app.history_index = Some(idx - 1);
                            app.input = app.input_history[idx - 1].clone();
                        }
                    }
                }
                KeyCode::Down => {
                    if let Some(idx) = app.history_index {
                        if idx + 1 < app.input_history.len() {
                            app.history_index = Some(idx + 1);
                            app.input = app.input_history[idx + 1].clone();
                        } else {
                            app.history_index = None;
                            app.input.clear();
                        }
                    }
                }
                KeyCode::PageUp => {
                    // 向上滚动对话区域
                    for _ in 0..5 {
                        app.scroll_up();
                    }
                }
                KeyCode::PageDown => {
                    // 向下滚动对话区域
                    for _ in 0..5 {
                        app.scroll_down();
                    }
                }
                KeyCode::Home if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    // Ctrl+Home: 滚动到顶部
                    app.scroll_offset = 0;
                }
                KeyCode::End if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    // Ctrl+End: 滚动到底部
                    app.scroll_to_bottom();
                }
                KeyCode::Char(c) => {
                    app.input.push(c);
                }
                KeyCode::Backspace => {
                    app.input.pop();
                }
                _ => {}
            }
        }
    }
}

fn render_ui(f: &mut Frame, app: &PlanApp) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(4),  // 增加到 4 行以显示状态
            Constraint::Min(10),
            Constraint::Length(3),
            Constraint::Length(1),
        ])
        .split(f.area());

    // 获取 Agent 状态显示
    let (status_text, status_color) = get_status_display(&app.agent_status, app.thinking_frame);

    // 顶部标题区域，显示关键信息
    let title_lines = vec![
        Line::from(vec![
            Span::styled(
                format!("📋 Feature: {} ", app.feature_slug),
                Style::default()
                    .fg(Color::Cyan)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::styled(
                format!("| 📂 {}", app.repo_path),
                Style::default().fg(Color::DarkGray),
            ),
        ]),
        Line::from(vec![
            Span::styled(
                "状态: ",
                Style::default().fg(Color::DarkGray),
            ),
            Span::styled(
                status_text,
                Style::default()
                    .fg(status_color)
                    .add_modifier(Modifier::BOLD),
            ),
        ]),
        Line::from(vec![
            Span::styled(
                "[Enter]",
                Style::default()
                    .fg(Color::Green)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::raw(" 发送  "),
            Span::styled(
                "[Ctrl+C/Esc]",
                Style::default()
                    .fg(Color::Red)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::raw(" 退出  "),
            Span::styled(
                "[↑↓]",
                Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::raw(" 历史  "),
            Span::styled(
                "[PgUp/PgDn]",
                Style::default()
                    .fg(Color::Cyan)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::raw(" 滚动"),
        ]),
    ];
    
    let title = Paragraph::new(title_lines)
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL).title("Code Agent - Plan"));
    f.render_widget(title, chunks[0]);

    let mut list_items: Vec<ListItem> = Vec::new();
    for msg in &app.messages {
        let (prefix, style) = match msg.role {
            ChatRole::User => ("You: ", Style::default().fg(Color::Green)),
            ChatRole::Assistant => ("Assistant: ", Style::default().fg(Color::Yellow)),
        };
        let line = Line::from(vec![
            Span::styled(prefix, style.add_modifier(Modifier::BOLD)),
            Span::raw(&msg.content),
        ]);
        list_items.push(ListItem::new(line));
    }
    if !app.streaming_buffer.is_empty() {
        list_items.push(ListItem::new(Line::from(vec![
            Span::styled(
                "Assistant: ",
                Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::raw(format!("{}█", app.streaming_buffer)),
        ])));
    }
    let list = List::new(list_items).block(Block::default().borders(Borders::ALL).title("对话"));
    f.render_widget(list, chunks[1]);

    let input = Paragraph::new(app.input.as_str())
        .style(Style::default().fg(Color::White))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("输入 (Enter 发送, ↑↓ 历史)"),
        )
        .wrap(Wrap { trim: false });
    f.render_widget(input, chunks[2]);

    // ✅ 设置光标位置到输入框（考虑中文字符显示宽度）
    use unicode_width::UnicodeWidthStr;
    let input_width = app.input.width();
    let cursor_x = chunks[2].x + input_width as u16 + 1; // +1 for border
    let cursor_y = chunks[2].y + 1; // +1 for border
    f.set_cursor_position((cursor_x, cursor_y));

    let stats_text = format!(
        "Turns: {} | Cost: ${:.4}",
        app.stats.turns, app.stats.cost_usd
    );
    let stats = Paragraph::new(stats_text)
        .style(Style::default().fg(Color::DarkGray))
        .block(Block::default().borders(Borders::ALL).title("Stats"));
    f.render_widget(stats, chunks[3]);
}

/// 获取 Agent 状态显示文本和颜色
fn get_status_display(status: &AgentStatus, thinking_frame: usize) -> (String, Color) {
    match status {
        AgentStatus::Idle => ("💤 空闲".to_string(), Color::DarkGray),
        AgentStatus::Thinking => {
            // 思考动画：旋转的点
            let frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
            let spinner = frames[thinking_frame % frames.len()];
            (format!("{} 思考中...", spinner), Color::Yellow)
        }
        AgentStatus::ExecutingTool(tool) => {
            (format!("🔧 执行工具: {}", tool), Color::Cyan)
        }
        AgentStatus::Completed => ("✅ 完成".to_string(), Color::Green),
        AgentStatus::Error(err) => {
            let truncated = if err.len() > 40 {
                format!("{}...", &err[..40])
            } else {
                err.clone()
            };
            (format!("❌ 错误: {}", truncated), Color::Red)
        }
    }
}

/// 查找已存在的 feature 目录
fn find_existing_feature(specs_dir: &Path, feature_slug: &str) -> Option<PathBuf> {
    if !specs_dir.exists() {
        return None;
    }

    for entry in std::fs::read_dir(specs_dir).ok()? {
        let entry = entry.ok()?;
        let path = entry.path();

        if path.is_dir()
            && let Some(dir_name) = path.file_name().and_then(|n| n.to_str()) {
                // 提取 slug：001-feature-slug → feature-slug
                if let Some(dash_pos) = dir_name.find('-') {
                    let prefix = &dir_name[..dash_pos];
                    if prefix.chars().all(|c| c.is_ascii_digit()) {
                        let extracted_slug = &dir_name[dash_pos + 1..];
                        if extracted_slug == feature_slug {
                            return Some(path);
                        }
                    }
                }
            }
    }

    None
}
