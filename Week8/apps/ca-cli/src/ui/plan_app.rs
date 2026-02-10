//! Plan TUI 应用
//!
//! 3 区域布局 (Chat / Input / Stats)，非阻塞事件循环，与 PlanWorker 通过 mpsc 通信。

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
    backend::{Backend, CrosstermBackend},
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
    Frame, Terminal,
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
}

impl PlanApp {
    pub fn new(feature_slug: String, repo_path: &Path) -> Self {
        let repo_path_str = repo_path.display().to_string();
        let mut messages = Vec::new();
        messages.push(ChatMessage {
            role: ChatRole::Assistant,
            content: format!("规划功能: {} | 工作目录: {}", feature_slug, repo_path_str),
        });
        messages.push(ChatMessage {
            role: ChatRole::Assistant,
            content: "请输入功能描述并按 Enter 发送，Ctrl+C 退出。".to_string(),
        });

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

        terminal
            .draw(|f| render_ui(f, app))
            .map_err(|e| anyhow::anyhow!("Terminal draw: {}", e))?;

        if app.should_quit {
            let _ = worker_tx.try_send(UserMessage::Quit);
            return Ok(());
        }

        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                        app.should_quit = true;
                    }
                    KeyCode::Esc => {
                        app.should_quit = true;
                    }
                    KeyCode::Enter => {
                        app.send_input(worker_tx);
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
}

fn render_ui(f: &mut Frame, app: &PlanApp) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(2),
            Constraint::Min(10),
            Constraint::Length(3),
            Constraint::Length(1),
        ])
        .split(f.area());

    let title = Paragraph::new(format!(
        "Code Agent Plan: {}  [Enter] 发送  [Ctrl+C] 退出",
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
            Span::styled("Assistant: ", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            Span::raw(format!("{}█", app.streaming_buffer)),
        ])));
    }
    let list = List::new(list_items)
        .block(Block::default().borders(Borders::ALL).title("对话"));
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

    let stats_text = format!(
        "Turns: {} | Cost: ${:.4}",
        app.stats.turns,
        app.stats.cost_usd
    );
    let stats = Paragraph::new(stats_text)
        .style(Style::default().fg(Color::DarkGray))
        .block(Block::default().borders(Borders::ALL).title("Stats"));
    f.render_widget(stats, chunks[3]);
}
