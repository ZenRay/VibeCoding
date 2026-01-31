# 端到端实践


## 探索
帮我研究一下市面上关于使用AI进行slides生成的工具,尤其是Manus和NotebookLM的slide
功能。探索它实现的原理。另外,探索如果使用google最新推出的nanabananapro来做slides
生成(思考:根据文本生成图片,把所有图片以幻灯片的形式连起来播放,就构成了slides,类
似NoteboookLM里的slides生成,要求:图片的视觉风格要统一,用户可以提供一个视觉风格
图片或者文字描述)。

## Plan -这里使用方案是需求和产品规划一起来进行了
根据 week7_prod.png 的内容,仔细阅读并思考,生成一一个产品。要求:使用中文。这个 app是一个本地运行的单页app,使用nano banana pro生成图片 slides,可以以走马灯的形式全屏播出。后端使用Python,前端使用Typescript。


/speckit.specify根据
week7_prod.png的内容,仔细阅读并思考,计划生成一一个产品。要求:使用中文。这个
app是一个本地运行的单页app,使用nano banana pro生成图片slides,可以以走马灯的形式全屏播出。后端使用
Python,前端使用Typescript。

更新 产品功能 prompt
prd需要修改:
1.图片生成使用 googleaisdk
2.对于侧边栏 slide,选中并拖拽可以改变顺序
3.文本内容变化后,如果图片中没有对应文本hash的图片,,在主图片区域下放一个按钮,用户点击可以生
成新的图片
4.outline.yml中需要保存用户选择的风格图片。当第一次打开时,如果没有风格图片,需要有个
popup,用户可以输入一段文字,生成两个图片,让用户边选择,用户选中的作为slides
的风格,以后生成新的图片时参考这张图片
5. Nano Banana Pro API key -> Genimi API key


/speckit.plan 注意所有前端所需的API
接口要定义清楚。整体项目的目录结构也要定义清楚,后端代码层次清晰,API/业务/存储要保持清晰的边界。本次项目的根目录是在 Week7，这里用于存放本次前后端开发等代码和开发相关文档


**更新 spec 和 plan**

google ai SDK使用:https://ai.google.dev/gemini-api/docs/image-generation,其中核心代码
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = ("Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme")
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
这里 nano banana pro 的模型名:gemini-3-pro-image-preview, 需要根据这些信息更新spec 和plan

**代码规范声明**

cursor V1

根据 specs 的相关内容,生成项目的空的目录结构。先不要生成代码。在
backend/和frontend/目录下分别生成 cursor 的前后端不同需求的rule :
* 内容考虑所使用语言框架的best practices
* -架构设计遵循的原则:SOLID/YAGNI/KISS/DRY
* 代码的组织结构
* 并发处理
* 错误处理和日志处理
* 其中所有所有版本使用最新依赖
* 后端开发需要使用 uv 管理且有一个独立的 venv 文件
* 前端需要注意使用统一的风格

cursor V2 这个版本是已经开发了 phase1后的 prompt
根据 specs 的相关内容在 backend/和frontend/目录下分别生成 cursor 的前后端不同需求的rule，这样方便前后端的subagent 调用 :
* 内容考虑所使用语言框架的best practices
* -架构设计遵循的原则:SOLID/YAGNI/KISS/DRY
* 代码的组织结构
* 并发处理
* 错误处理和日志处理
* 其中所有所有版本使用最新依赖
* 后端开发需要使用 uv 管理且有一个独立的 venv 文件
* 前端需要注意使用统一的风格

CLAUDE

根据 specs 的相关内容,生成项目的空的目录结构。先不要生成代码。在backend/和frontend/目录下分别生成 CLAUDE.md  的前后端不同需求的rule : 
* 内容考虑所使用语言框架的best practices
* -架构设计遵循的原则:SOLID/YAGNI/KISS/DRY
* 代码的组织结构
* 并发处理
* 错误处理和日志处理
* 其中所有所有版本使用最新依赖
* 后端开发需要使用 uv 管理且有一个独立的 venv 文件
* 前端需要注意使用统一的风格

注意一定不要生成不必要的代码文件，只需要生成必要的目录，并更新需要的CLAUDE.md 即可

**Tasks生成**
/speckit.tasks 根据开发需求设计不超过 5 个phase的阶段，代码的开发需要考虑到前后端并行开发的可能性。这样方便我们使用 subagent 的方式开发


**并行开发前后端**
您可以通过调用 Task 工具来启动子智能体 (Subagent)。根据我们设计的 tasks.md 结构（特别是明确的 Backend/Frontend 轨道和 [P] 并行标记），有以下几种高效的执行方式：
1. 按阶段顺序执行 (最稳健)
这是最简单的方式，适合 Phase 1 (Setup) 这种基础建设阶段，或者当您不急于并行时。一个智能体会按顺序逐个完成任务。
指令示例: "使用 subagent 完成 specs/001-ai-slide-generator/tasks.md 中的 Phase 1 所有任务。"
2. 前后端并行执行 (最高效)
对于 Phase 2, 3, 4，我们明确划分了 Backend Track 和 Frontend Track。您可以一次性发出指令，让我同时启动两个 subagent 并行工作。
指令示例: "请并行启动两个 subagent 执行 Phase 2 的任务：
第一个 agent 负责 Backend Track (T008, T009)。
第二个 agent 负责 Frontend Track (T010, T011, T012)。"
3. 指定任务 ID 执行 (最精准)
如果您只想完成特定的几个任务，可以直接指定 ID。
指令示例: "让 subagent 完成任务 T001, T002 和 T003。"
现在的建议：
鉴于我们刚开始，Phase 1 (Setup & Foundation) 包含了前后端的初始化。虽然可以并行，但在初始化阶段让一个 agent 统筹目录结构可能更安全（避免文件锁或路径冲突）。


**并行开发前后端代码**
/speckit.implement 针对 phase2 和 phase3使用 两个不同 subagent 进行开发，分别完成前端和后端的开发。当前项目的状态可以参考@Week7/PHASE1_REPORT.md 

##  Design2Plan

### 1.1
根据 ./specs/w7/0001-prd.md 和@specs/w7/genslide.jpg的内容,生成一个designspec,放在
./specs/w7/0002-design-spec.md文件中。要求:使用中文,注意所有前端所需的API
接口要定义清楚。整体项目的目录结构也要定义清楚,后端代码层次清晰,API/业务/存储要保持清晰的边界。


### 1.2 
google ai SDK使用:https://ai.google.dev/gemini-api/docs/image-generation,其中核心代码
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = ("Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme")
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
这里 nano banana pro 的模型名:gemini-3-pro-image-preview,更新designspec


### 1.3 
根据 ./specs/w7/0002-design-spec.md的内容,生成项目的空的目录结构。先不要生成代码。在
backend/和frontend/目录下分别生成 CLAUDE.md 文文件,内容考虑
所使用语言框架的best practices
-架构设计遵循的原则:SOLID/YAGNI/KISS
代码的组织结构
并发处理
-错误处理和日志处理

### 1.4 
根据 aspecs/w7/0002-design-spec.md的内容,启动
python 和 typescript 两个 agent
代码。代码在./w7/genslides下。
分别撰写后端和前端的


测试

前端页面出错-如果不带slug,似乎要展示demo,但不存在