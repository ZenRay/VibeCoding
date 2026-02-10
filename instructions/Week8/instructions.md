# Code Agent 设计

## 初始化项目

Ref Prompt
这是一个geektimebootcamp agent(GBA)项目,它的主要功能是封装claudeagentsdk,让用户可以很方便的围绕一个repo 来添加新的功能。请把这个Rust项目转换成一个workspace,里面包含 crates/gba-core (core execute engine), crates/gba-pm (promptmanager),以及 apps/gba-cli (command line interface)。生成的是一个gbacli。所有的deps放在workspace下,各个 crate 通过:`xx={workspace=true}`来引用。CLI使用clap/ratatui来构建。prompt manager使用 minijinja来构建。core execute engine 使用 tokio/claude-agent-sdk-rs 0.6 来构建。所有deps都要便用最新版本。


Real Prompt
这是一个 Code Agent项目,它的主要功能是封装相关 Agent 的SDK(eg: Claude Agent, Copilot Agent 以及 Cursor Agent ),让用户可以方便的围绕一个repo 来添加新的功能。这个项目需要基于 Rust 来进行开发,里面包含 crates/ca-core (core execute engine), crates/ca-pm (promptmanager),以及 apps/ca-cli (command line interface)。生成的是一个code-agent cli。所有的 deps放在 workspace 下,各个 crate 通过:`xx={workspace=true}`来引用。CLI使用clap/ratatui来构建。prompt manager使用 minijinja来构建。core execute engine 使用 tokio/claude-agent-sdk-rs 0.6 来构建。所有deps都要便用最新版本。项目开发需要在 ~/Documents/VibeCoding/Week8 中进行

## 设计文档

### 2.1 
Ref Prompt

根据截图,生成设计文档:
- -包括核心架构的ascii diagram,以及重要的流程
- 各个 crate有清晰的职责和 public interface
- gba-core:核心的执行引擎,根据不同场景下的 prompt,调用claudeagentsdk来执行任务。务必提供非常精简可用的接口
- gba-pm:提示词管理器,负责加载、渲染、管理提示词。务必提供非常
- gba-cli:命令行界面,负责与用户交互,并调用 gba-corre来执行任务
- 代码结构尽可能职责单一,不要出现重复代码,followSOLID principles,尽可能使用 Rust的最新特性。
- 提供开发计划,包括每个阶段的任务。

设计文档放在./specs下合适的位置

Real Prompt
根据截图,生成设计文档:
- -包括核心架构的 mermaid,以及重要的流程
- 各个 crate有清晰的职责和 public interface
- ca-core:核心的执行引擎,根据不同场景下的 prompt,调用 agent sdk(需要考虑兼容 copilot agent SDK 和 Claude Agent SDK， Cursor Agent SDK)来执行任务。务必提供非常精简可用的接口
- ca-pm:提示词管理器,负责加载、渲染、管理提示词。务必提供非常
- ca-cli:命令行界面,负责与用户交互,并调用 ca-core 来执行任务
- 代码结构尽可能职责单一,不要出现重复代码,follow SOLID principles,尽可能使用 Rust的最新特性。
- 提供开发计划,包括每个阶段的任务。

设计文档放在./instructions/Week8 下合适的位置


### 2.2
Ref Prompt
1. .gba/config.toml是干啥的?为什么需要?如果需要要这样一个配置,请在设计里面说明,并使用 config.yml格式。每个 feature下面的state.json也使用 state.yml。需要定义它的结构。
2. task kind应该还有 verification
3. 任务执行结果应该记录turns/cost,放在state.yml中,最后的PR link也放进去。
4. 在`gba run'过程中,如果中断,下次运行可以继续恢复(在提示词里体现)。
5. 预先思考好所有场景下的提示词,放在 crates/gba-pm/templates下,我来 review。提示词用英文

请更新design spec



Real Prompt

1. 设计中还缺少对每个 feature 功能状态信息，可以考虑使用 state.yml 完成跟踪执行进度、支持中断后回复；记录每个阶段执行结果和成本以及存储最终的 PR 链接。需要定义它的结构，需要不同的 Agent 都能够读取相关信息——保证不同 Agent 能够理解信息的一致性
2. task kind 应该还有 verification
3. 在`code-agent run'过程中,如果中断,下次运行可以继续恢复(在提示词里体现)。
4. 预先思考好所有场景下的提示词,放在 crates/ca-pm/templates下,我来 review。提示词用英文
请更新design.md 文档

### 2.3
Ref Prompt
注意 init 的提示词应该还要生成 .gba / .trees 等目录，以及更改 .gitignore；run/execute 的提示词最后要使用 gh cli 生成 pull request 并且提供详尽的 PR description.

请仔细review 提示词中的变量以及条件判断：
1. 是否有必要 - 我们要尽可能 follow convention over configuration
2. 是否能在 execution engine 的上下文提供

目前这些提示词哪些是作为 sys prompt 添加到 claude code 系统提示词中，哪些是作为 user prompt 来驱动完成工作？比如 gba init 的 user prompt 是什么？

Real Prompt

注意 init 的提示词应该还要生成 specs / .trees 等目录，以及更改 .gitignore；run/execute 的提示词最后要使用 gh cli 生成 pull request 并且提供详尽的 PR description.

请仔细review 提示词中的变量以及条件判断：
1. 是否有必要 - 我们要尽可能 follow convention over configuration
2. 是否能在 execution engine 的上下文提供

目前这些提示词哪些是作为 sys prompt 添加到系统提示词(这里需要考虑不同的 Agent SDK 之间是否需要有差异性)中，哪些是作为 user prompt 来驱动完成工作？比如 code-agent init 的 user prompt 是什么？

### 2.4
另外，请思考在不同的场景下，哪些需要 claude code preset，哪些不需要，哪些需要完整的工具，哪些不需要，这个应该在那里定义，是写在engine 中，还是配置中？

另外，请思考在不同的场景下，哪些需要 agent preset，哪些不需要，哪些需要完整的工具，哪些不需要，这个应该在那里定义，是写在engine 中，还是配置中？此外在当设计内容中是否还没有考虑 plan 阶段

## 构建 Code Agent
构建一个新的 git worktree (branch from main)，放在 .trees 下，仔细阅读 @specs/design.md，根据其要求，使用 sub agent 分阶段完成其功能。每次完成一个阶段后提交代码，并确保 precommit hooks 通过。完成所有阶段后，启动一个新的 sub agent 调用 codex code review skill 对照 design spec 来 review 代码，然后根据 review 结果仔细思考，对合理的问题进行修改，并提交代码。最后，保证所有的测试通过，并确保所有的功能都符合 design spec 的要求后，生成一个 pull request，提供详细的 PR description。

构建一个新的 git worktree (branch from main)，放在 .trees 下，仔细阅读 design.md，根据其要求，使用 sub agent 分阶段完成其功能。每次完成一个阶段后提交代码，并确保 precommit hooks 通过。完成所有阶段后，启动一个新的 sub agent 调用 codex code review skill 对照 design spec 来 review 代码，然后根据 review 结果仔细思考，对合理的问题进行修改，并提交代码。最后，保证所有的测试通过，并确保所有的功能都符合 design spec 的要求后，生成一个 pull request，提供详细的 PR description。