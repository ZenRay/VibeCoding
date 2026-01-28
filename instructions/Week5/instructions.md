# MCP

https://gemini.google.com/share/0c07955bad16

生成CLAUDE.md.要求:代码要符合 python best practice/idomatic python,符合 SOLID/DRY等设计思路代码质量和测试质量要高,性能要好。开发环境需要生成一个开发环境，相关的 package 管理实用 UV 进行。本次开发啊需要放到当前目录下 


## 构建MCP SERVER
主要的需求是在Python下面创建一个Postgres的mcp：用户可以给特定自然语言描述的查询的需求，然后mcp server 根据结果来返回一个SQL或者返回这个查询的结果。mcp的服务器在启动的时候，应该读取它都有哪些可以访问的数据库，并且缓存这些数据库的schema：了解每一个数据库下面都有哪些 table/view/types/index 等等，然后根据这些信息以及用户的输入去调用OpenAI的大模型（gpt-5-mini）来生成 SQL。之后mcp server应该来校验这个sql只允许查询的语句然后测试这个sql确保它能够执行并且返回有意义的结果：这里也可以把用户的输入生成的sql以及返回的结果的一部分调用openai来确认这样可以确保它的结果是不是有意义。最后根据用户的输入是返回SQL还是返回SQL查询之后的结果来返回相应的内容根据这些需求帮我构建一个详细的需求文档，先不要著急去做设计，等我review完这个需求文档之后呢我们再来讨论设计，文档放在specs。项目的目录 Week5

帮我研究一下这个需求如果使用Python来实现的话那应该用那些库为什么用这些库
> 建议，可以使用多种工具先进行探索

### Review 设计  
commit code;然后,接口目前只需要query即可,其它意义不
大;另外调用codex reviewskill让 让 codex review 这个需求文 
档,并更新

### PRD 设计
/speckit.plan 使用FastMCP、Asyncpg、SQLGlot、Pydantic以及FastMCP 构建pg-mcp的架构设计——相关框架优先使用最新版本。如果有使用 SQLalchemy 时，优先使用新版本Think Ultra Hard.        


### PRD review
使用subagent调用codexreviewskill让
codex review ./specs/w5/0002-pg-mcp-
design.md文件。之后仔细阅读review的结果,思考
是否合理,然后相应地并更新./specs/w5/0002-pg-
mcp-design.md文件。

### Design review 以及执行计划设计
根据 ./specs/w5/0002-pg-mcp-design.md文档,构建 pg-mcp的实现计划,think ultra hard,文档放在
/specs/w5/0004-pg-mcp-impl-plan.md文件中。之后调月codex review skill it codex review ./specs/w5/00004-pg-mcp-impl-plan.md
文件,并构建./specs/w5/0005-pg-mcp-impl-plan-review.md文件。


### Implement Plan

./specs/w5/0002-pg-mcp-design.md 文档,使用
subagent完整实现pg-mcpphase0-4。提交,之后
调用 codex review skill 让 codex review 整个代
码,看其是否符合design和implplan。把 review
结果写到./specs/w5/0006-pg-mcp-code-
review.md文件中。


### 测试数据库准备
根据 specs 的需求在 fixtures下构建三个有意义的数据库,分别有少量,中等量级,以及大量的 table/view/types/index等schema,且有足够多的数据。生成这三个数据库的 SQL 文件,并基于 Docker 构建数据库。最终使用 Makefile 来重建这些测试数据库。另外需要看看是否需要更新一下 specs 下的文档


commit然后你来建立和测试这几个数据库确保可用

**生成对比数据**
---
/speckit.implement phase2 已经完成。当前项目进度可以查看@specs/001-postgres-mcp/CURRENT_STATUS.md 。现在需要未测试做准备：根据这些fixture,假设用户要用自然语言提问,然后pg-mcp来生成相应的sql,帮我生成一个test.md的文档,里面包含各种对数据库内部数据的简单到复杂的提问。确保生成的test plan你可以自己执行并验证功能

## 自动测试 prompt
确保生成的test plan你可以自己执行并验证功能


##  MCP 测试
对于Qw5/pg-mcp,将这个mcp添加到claude code中,打开一个 claude code headless cli 选择 @g-mcp/fixturres/TEST_QUERIES.md
下面的某些query,运行,查看是否调用这个 mcp,结果是否符合预期


直接用本地的 `uvx --refresh --from /Users/tchen/projects/mydcode/bootcamp/ai/w5/pg-mcp pg-mcp` 来运营mcp server



# SKILL
在当前项目下创建一个新的skill,要求:
1.首先通过psql(localhost:5432,postgres,postgres)
探索这几个数据库:blog_small、ecommerce_medium、saas_crm_large,了解它们都有哪些 table/view/types/index等等,每个数据库一个md
文件,作为skill的reference。
2.用户可以给特定自然语言描述的查询的需求,skill根据用户输入找到相应的数据库的 reference
文件,然后根据这些信息以及用户的输入来生成正确的SQL。SQL只允许查询语句,不能有任何的写操作,不能有任何安全漏洞比如SQL
注入,不能有任何危险的操作比如 sleep,不能有任何的敏感信息比如APIKey等。
3.使用psql测试这个SQL确保它能够执行并且返回有意义的结果。如果执行失败,则深度思考,重新生成SQL,回到第3步
4.把用户的输入,生成的SQL,以及返回的结果的一部分进行分析来确认结果是不是有意义,根据分析打个分数。10分非常
confident,0分非常不 confident。如果小于7分,则深度思考,重新生成SQL,回到第3步。
5.最后根据用户的输入是返回 SQL还是返回SQL查询;之后的结果(默认)来返回相应的内容


