# Project Alpha 验证和测试指南

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [前后端交互验证](#前后端交互验证)
2. [阶段 2 验证指南](#阶段-2-验证指南)
3. [快速验证步骤](#快速验证步骤)

---

## 前后端交互验证

### ✅ 验证结果

#### 1. 服务状态
- ✅ **PostgreSQL**: 运行正常，健康检查通过
- ✅ **后端 API**: 运行正常，端口 8000
- ✅ **前端**: 运行正常，端口 5173

#### 2. 后端 API 验证
- ✅ `/api/v1/tags` - 返回标签列表
- ✅ `/api/v1/tickets` - 返回 Ticket 列表
- ✅ `/api/v1` - API 根端点正常
- ✅ CORS 配置正确（`access-control-allow-origin: *`）

#### 3. 前后端交互验证
- ✅ 后端日志显示前端正在调用 API：
  ```
  GET /api/v1/tags HTTP/1.1" 200 OK
  GET /api/v1/tickets HTTP/1.1" 200 OK
  ```
- ✅ Vite 代理配置已修复（使用 `backend` 服务名）
- ✅ 前端 API 服务配置正确（使用相对路径 `/api/v1`）

#### 4. 前端页面更新
- ✅ `HomePage.tsx` 已更新，现在会：
  - 调用 `useTickets()` 获取 Ticket 列表
  - 调用 `useTags()` 获取标签列表
  - 显示数据（包括标签颜色、Ticket 状态、软删除样式等）

### 🔍 如何验证数据是否正常显示

#### 方法 1：访问前端页面
1. 打开浏览器访问：http://localhost:5173
2. 应该看到：
   - **标签列表**：显示所有标签，包括颜色、使用次数
   - **Ticket 列表**：显示所有 Ticket，包括标题、描述、状态、标签

#### 方法 2：检查浏览器开发者工具
1. 打开浏览器开发者工具（F12）
2. 查看 **Console** 标签页：
   - 不应该有红色错误信息
   - 如果有错误，查看具体错误内容
3. 查看 **Network** 标签页：
   - 应该看到 `GET /api/v1/tags` 请求，状态码 200
   - 应该看到 `GET /api/v1/tickets` 请求，状态码 200
   - 点击请求查看响应数据

#### 方法 3：使用验证脚本
```bash
cd Week1
./verify_frontend_backend.sh
```

### 🐛 如果数据没有显示

#### 检查清单

1. **检查服务是否运行**
   ```bash
   cd env
   docker compose ps
   ```
   所有服务应该显示 "Up"

2. **检查后端 API 是否正常**
   ```bash
   curl http://localhost:8000/api/v1/tags
   curl http://localhost:8000/api/v1/tickets
   ```
   应该返回 JSON 数据

3. **检查前端页面**
   - 访问 http://localhost:5173
   - 打开浏览器开发者工具（F12）
   - 查看 Console 是否有错误
   - 查看 Network 标签页，检查 API 请求是否成功

4. **检查前端日志**
   ```bash
   cd env
   docker compose logs frontend --tail 50
   ```
   查看是否有错误信息

5. **检查后端日志**
   ```bash
   cd env
   docker compose logs backend --tail 50
   ```
   查看是否有 API 请求记录

### 📝 已修复的问题

1. ✅ **前端 Dockerfile**: 修复 `npm ci` → `npm install`
2. ✅ **后端 Dockerfile**: 修复依赖安装方式
3. ✅ **后端配置**: 修复 `cors_origins` 解析
4. ✅ **迁移脚本**: 添加表存在检查，避免重复创建
5. ✅ **API 导入**: 修复 `TicketListResponse` → `TicketList`
6. ✅ **Vite 代理**: 修复 Docker 环境中的代理配置
7. ✅ **前端页面**: 更新 HomePage 实际调用 API 并显示数据
8. ✅ **API 根端点**: 添加 `/api/v1` 端点

---

## 阶段 2 验证指南

### 🎯 验证目标

验证阶段 2 的所有功能是否正常工作：
- ✅ 所有 API 端点实现完成
- ✅ API 文档完整可用
- ✅ 搜索和过滤功能正常
- ✅ 软删除和恢复功能正常
- ✅ 标签标准化功能正常
- ✅ 单元测试和集成测试通过

### 🚀 快速验证步骤

#### 步骤 1：启动后端服务

```bash
cd backend

# 激活虚拟环境
source .venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 步骤 2：运行验证脚本

在另一个终端：

```bash
cd backend
python verify_phase2.py
```

#### 步骤 3：访问 API 文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 步骤 4：运行单元测试和集成测试

```bash
cd backend

# 运行所有测试
pytest -v

# 查看覆盖率
pytest --cov=app --cov-report=html
```

### 📋 详细验证清单

#### 1. API 文档验证

- [ ] 访问 http://localhost:8000/docs
- [ ] 检查所有 Ticket API 端点是否显示
- [ ] 检查所有 Tag API 端点是否显示
- [ ] 检查每个端点是否有详细的描述
- [ ] 在 Swagger UI 中测试创建 Ticket
- [ ] 在 Swagger UI 中测试创建 Tag

#### 2. Ticket API 验证

使用 httpie 或 curl 测试：

```bash
# 创建 Ticket
http POST localhost:8000/api/v1/tickets \
  title="验证测试" \
  description="用于验证 API"

# 获取 Ticket 列表
http GET localhost:8000/api/v1/tickets

# 更新 Ticket
http PUT localhost:8000/api/v1/tickets/1 \
  title="更新后的标题"

# 切换状态
http PATCH localhost:8000/api/v1/tickets/1/toggle-status

# 搜索 Ticket
http GET localhost:8000/api/v1/tickets search=="测试"

# 软删除
http DELETE localhost:8000/api/v1/tickets/1

# 查看回收站
http GET localhost:8000/api/v1/tickets only_deleted==true

# 恢复 Ticket
http POST localhost:8000/api/v1/tickets/1/restore
```

#### 3. Tag API 验证

```bash
# 创建标签（注意：名称会自动转大写）
http POST localhost:8000/api/v1/tags \
  name="test tag" \
  color="#FF0000"
# 应该返回 "TEST TAG"

# 获取标签列表
http GET localhost:8000/api/v1/tags

# 更新标签
http PUT localhost:8000/api/v1/tags/1 \
  name="updated tag" \
  color="#00FF00"
# 应该返回 "UPDATED TAG"

# 删除标签
http DELETE localhost:8000/api/v1/tags/1
```

#### 4. 搜索和过滤验证

```bash
# 按状态过滤
http GET localhost:8000/api/v1/tickets status==pending
http GET localhost:8000/api/v1/tickets status==completed

# 按标签过滤（AND）
http GET localhost:8000/api/v1/tickets tag_ids==1,2 tag_filter==and

# 按标签过滤（OR）
http GET localhost:8000/api/v1/tickets tag_ids==1,2 tag_filter==or

# 搜索
http GET localhost:8000/api/v1/tickets search=="关键词"

# 排序
http GET localhost:8000/api/v1/tickets sort_by==title sort_order==asc

# 分页
http GET localhost:8000/api/v1/tickets page==1 page_size==10
```

### 🐛 常见问题排查

#### 问题 1：API 返回 404

**可能原因**：
- 路由未正确注册
- URL 路径错误

**解决方案**：
1. 检查 `app/api/v1/__init__.py` 中的路由注册
2. 检查 `app/main.py` 中的路由包含
3. 查看 Swagger UI 确认端点路径

#### 问题 2：数据库错误

**可能原因**：
- 数据库迁移未运行
- 数据库连接配置错误

**解决方案**：
```bash
# 运行数据库迁移
alembic upgrade head

# 检查数据库连接
python -c "from app.database import engine; engine.connect(); print('✅ 数据库连接成功')"
```

#### 问题 3：标签名称未转大写

**可能原因**：
- 数据库触发器未创建

**解决方案**：
```bash
# 检查触发器是否存在
psql -U ticketuser -d ticketdb -c "\df normalize_tag_name"

# 重新运行迁移
alembic upgrade head
```

#### 问题 4：测试失败

**可能原因**：
- 测试数据库配置错误
- 测试数据未清理

**解决方案**：
```bash
# 清理测试数据库
rm -f test.db

# 重新运行测试
pytest --tb=short -v
```

### ✅ 验证完成标准

- [x] 所有 API 端点可以正常访问
- [x] Swagger UI 显示所有端点
- [x] 可以创建、读取、更新、删除 Ticket
- [x] 可以创建、读取、更新、删除 Tag
- [x] 软删除和恢复功能正常
- [x] 标签名称自动转大写
- [x] 搜索和过滤功能正常
- [x] 单元测试通过
- [x] 集成测试通过
- [x] 测试覆盖率 ≥ 70%

---

## 快速验证步骤

### 方式 1：使用 Docker（推荐）

```bash
# 启动所有服务
cd env
./start.sh

# 访问前端页面
open http://localhost:5173

# 访问 API 文档
open http://localhost:8000/docs
```

### 方式 2：本地开发

```bash
# 启动后端
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# 启动前端（另一个终端）
cd frontend
npm run dev
```

### 验证清单

- [ ] 所有服务正常运行
- [ ] 前端页面可以访问
- [ ] API 文档可以访问
- [ ] 可以创建 Ticket 和 Tag
- [ ] 搜索和过滤功能正常
- [ ] 前后端交互正常

---

**验证时间**: 2026-01-08  
**状态**: ✅ 验证通过
