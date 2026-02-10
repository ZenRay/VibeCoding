use std::io;
use std::path::Path;
use std::time::Duration;

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
    widgets::{Block, Borders, List, ListItem, Paragraph},
};

use crate::config::AppConfig;

pub async fn run_tui(repo_path: &Path, config: &AppConfig) -> anyhow::Result<()> {
    // 设置终端
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // 创建应用状态
    let mut app = App::new(repo_path, config);

    // 运行应用
    let res = run_app(&mut terminal, &mut app).await;

    // 恢复终端
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        println!("错误: {:?}", err);
    }

    Ok(())
}

#[allow(dead_code)]
struct App<'a> {
    repo_path: &'a Path,
    config: &'a AppConfig,
    input: String,
    messages: Vec<String>,
    should_quit: bool,
}

impl<'a> App<'a> {
    fn new(repo_path: &'a Path, config: &'a AppConfig) -> Self {
        Self {
            repo_path,
            config,
            input: String::new(),
            messages: vec![
                "欢迎使用 Code Agent TUI!".to_string(),
                format!("工作目录: {}", repo_path.display()),
                "输入任务描述并按回车执行,按 Esc 退出".to_string(),
            ],
            should_quit: false,
        }
    }

    fn add_message(&mut self, msg: String) {
        self.messages.push(msg);
        // 保持最近 50 条消息
        if self.messages.len() > 50 {
            self.messages.remove(0);
        }
    }
}

async fn run_app<B: Backend>(terminal: &mut Terminal<B>, app: &mut App<'_>) -> anyhow::Result<()> {
    loop {
        terminal
            .draw(|f| ui(f, app))
            .map_err(|e| anyhow::anyhow!("Terminal draw error: {}", e))?;

        if app.should_quit {
            return Ok(());
        }

        if event::poll(Duration::from_millis(100))?
            && let Event::Key(key) = event::read()?
        {
            match key.code {
                KeyCode::Esc => {
                    app.should_quit = true;
                }
                KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                    app.should_quit = true;
                }
                KeyCode::Enter => {
                    if !app.input.is_empty() {
                        let task = app.input.clone();
                        app.add_message(format!("> {}", task));
                        app.input.clear();

                        // 这里应该异步执行任务,为了简化,先显示提示
                        app.add_message("⚙️  执行中...".to_string());
                        app.add_message("✅ (模拟) 任务完成".to_string());
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

fn ui(f: &mut Frame, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(1),
            Constraint::Length(3),
        ])
        .split(f.area());

    // 标题
    let title = Paragraph::new("Code Agent TUI")
        .style(
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL));
    f.render_widget(title, chunks[0]);

    // 消息列表
    let messages: Vec<ListItem> = app
        .messages
        .iter()
        .map(|m| {
            let content = Line::from(Span::raw(m));
            ListItem::new(content)
        })
        .collect();

    let messages_list =
        List::new(messages).block(Block::default().borders(Borders::ALL).title("消息"));
    f.render_widget(messages_list, chunks[1]);

    // 输入框
    let input = Paragraph::new(app.input.as_str())
        .style(Style::default().fg(Color::Yellow))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("输入 (Enter: 执行, Esc: 退出)"),
        );
    f.render_widget(input, chunks[2]);
}
