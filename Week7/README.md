# AI Slide Generator (AI 幻灯片生成器)

基于 **Google Gemini AI** 的智能幻灯片生成应用。

## 技术栈

- **后端**: Python + FastAPI
- **前端**: TypeScript + React + Vite + Tailwind CSS
- **AI**: Google Gemini (`gemini-3-pro-image-preview`)

## 项目结构

```
Week7/
├── backend/         # Python FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 端点
│   │   ├── core/     # 核心逻辑 (生成器、配置)
│   │   ├── data/     # 数据访问层 (YAML 存储)
│   │   └── models/   # Pydantic 数据模型
│   ├── .venv/        # Python 虚拟环境 (uv)
│   └── requirements.txt
├── frontend/        # React 前端
│   ├── src/
│   │   ├── api/      # API 客户端
│   │   ├── components/  # UI 组件
│   │   └── types/    # TypeScript 类型
│   └── package.json
├── assets/          # 生成的图片存储
└── outline.yml      # 项目状态 (单一数据源)
```

## 快速开始

### 1. 后端设置

```bash
cd Week7/backend

# 创建虚拟环境 (使用 uv)
uv venv .venv
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 GEMINI_API_KEY

# 启动开发服务器
python run.py
```

后端将运行在 `http://localhost:8000`
Swagger 文档: `http://localhost:8000/docs`

### 2. 前端设置

```bash
cd Week7/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

## API 端点

- `GET /api/project` - 获取项目状态
- `POST /api/style/init` - 生成风格候选图
- `POST /api/style/select` - 保存选定风格
- `POST /api/slides` - 创建新幻灯片
- `PUT /api/slides/reorder` - 更新幻灯片顺序
- `PUT /api/slides/{id}` - 更新幻灯片文本
- `POST /api/slides/{id}/generate` - 重新生成图片
- `DELETE /api/slides/{id}` - 删除幻灯片

## 开发规则

本项目使用 Cursor AI 规则文件来指导开发：
- **后端规则**: `backend/.cursorrules` - Python/FastAPI 最佳实践
- **前端规则**: `frontend/.cursorrules` - TypeScript/React 最佳实践

详细说明请查看: [CURSORRULES.md](./CURSORRULES.md)

## 开发状态

**Phase 1 完成** ✅
- [x] 项目目录结构
- [x] 后端 FastAPI 初始化
- [x] 前端 React + Vite 初始化
- [x] YAML 存储层
- [x] Gemini AI 生成器封装 (Stub)
- [x] API 端点定义
- [x] CORS 配置
- [x] Cursor AI 开发规则

**下一步**: Phase 2 - 风格初始化 UI 开发

## 许可证

MIT
