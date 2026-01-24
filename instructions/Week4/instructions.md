# 对项目解读演练

仔细阅读./venders/codex的代码,撰写一个详细的架构分析文档,如需图表,使用 mermaid chart。文档放在:./specs/w4/codex-arch-by-codex.md



## 事件循环
帮我梳理codex代码处理事件循环的部分,详细解读当用户发起一个任务后,codex是如何分解处理这个任务,并不断自我迭代,最终完成整个任务。这个过程中发生了什么,codex如何决定任务完成还是未完成需要继续迭代。如果需要,可以用mermaid chart来辅助说明。写入/specs/w4/codex-event-loop.md


## 工具调用
帮我梳理codex代码处理工具调用的部分,详细解读codex是如何知道有哪些工具可以调用,如何选择工具,如何调用工具,如何处理工具的返回结果,如何决定工具调用是否成功等等。如果需要,可以用mermaid chart来辅助说明。写入./specs/w4/codex-tool-call.md

## Repo History 解读
查看 repo的所有 commit history,梳理其代码变更的脉络,必要时辅以mermaid chart。写入./specs/w4/codex-changes-by-claude.md


## 了解 codex的apply_patch工具
帮我梳理./vendors/codex的apply_patch工具,详细解读apply_patch工具的原理,如何使用,如何实现,如何测试等等等。以及apply_patch工具的代码是如何跟 codex其他部分集成的,另外我注意到apply_patch_tool_instructions.md文件,这个文件是做什么的,如何跟apply_patchcrate打交道。如果需要,可以以用 mermaid chart来辅助说明。入./specs/w4/applypatch.md

## apply_patch 集成
如果我要把apply_patch工具集成到我自己的项目中,我需要做哪些工作,如何做等等。如果需要,可以用mermaid chart来辅助说明。写入./specs/w4/codex-apply-patch-integration.md