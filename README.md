# Heart Garden - 心语花园

## 项目概述

Heart Garden 是一个基于 AI 驱动的情感陪伴应用，为用户提供深度理解、情绪追踪和智能陪伴服务。系统采用本地化部署方案，确保用户数据隐私安全。

## 技术架构

### 前端技术栈

- **框架**: Vue 3 (Composition API + `<script setup>`)
- **构建工具**: Vite 6
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **样式方案**: Tailwind CSS 3
- **设计风格**: 手绘风格 (Hand-Drawn Design)

### 后端技术栈

- **Web 框架**: Flask 3.0.0
- **CORS 支持**: flask-cors 4.0.0
- **数据库**: SQLite
- **配置管理**: python-dotenv 1.0.0
- **JWT 认证**: PyJWT 2.8.0
- **频率限制**: flask-limiter 3.10.1
- **LLM 集成**: OpenAI SDK (兼容模式)

### 服务模块

1. **情绪分析服务** (mood_analyzer.py)
   - 文本情绪识别、关键词提取、情绪趋势分析、规则 fallback 词库

2. **AI 陪伴服务** (ai_companion.py)
   - 上下文感知对话、多轮对话记忆、个性化回复生成

3. **大模型服务** (llm_service.py)
   - 混合模式路由：自动判断使用规则引擎或大模型
   - 用户配置驱动：从数据库读取用户 LLM 配置
   - LLM 情绪判定：AI 陪伴启用大模型时优先由模型判断用户消息情绪
   - 自动降级：大模型失败时回退到规则引擎

4. **LLM 接口层** (openai_compatible.py)
   - OpenAI 兼容接口实现，支持任意兼容 API
   - 接口抽象 (llm_interface.py)，方便切换模型

5. **Prompt 引擎** (prompt_engine.py)
   - 将规则引擎逻辑转化为 LLM 系统提示词
   - 支持个性化配置和情绪上下文注入

6. **共享常量** (constants.py)
   - 模板词库、表情映射、情绪关键词

7. **日志系统** (app/__init__.py + 服务日志)
   - stdout/file 双通道输出、请求 ID、请求耗时、LLM 调用/降级追踪

## 核心功能

### 1. 用户系统
- 用户注册/登录 (JWT 认证)
- 用户数据隔离
- 获取用户信息

### 2. 日记记录
- 创建/读取/更新/删除日记
- 自动时间戳管理

### 3. 情绪分析
- 多维度情绪识别 (0-100 分制)
- AI 陪伴大模型模式下优先使用 LLM 语义情绪判定
- 情绪标签分类、趋势分析
- 规则词库作为未配置大模型或 LLM 失败时的 fallback

### 4. 智能对话 (混合模式)
- **规则引擎模式**（默认）：无需配置，即开即用
- **大模型模式**（可选）：配置 API Key 后启用 AI 对话
- **自动降级**：大模型异常时自动回退到规则引擎
- 大模型模式下优先由 LLM 判定用户情绪，规则词库兜底
- 上下文感知、多轮对话记忆
- 对话中显示响应来源标识（AI / 规则）

### 5. 设置与配置
- AI 对话模式切换（规则/大模型）
- LLM 配置管理（URL、API Key、模型、温度）
- API Key 安全回显：设置页重新进入时不泄露、不覆盖已保存密钥
- 连接测试功能
- 自定义情绪词库入口暂时关闭

### 6. 数据追踪与统计
- 情绪历史记录与趋势可视化
- 统计分析接口
- 情绪分布统计
- AI 陪伴聊天情绪纳入趋势与分布统计

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- SQLite 3.8+

### 一键启动 (Windows)

```bash
# 双击运行
start.bat
```

### 手动启动

```bash
# 克隆项目
git clone https://github.com/DDDFXYqiming/heart-garden.git
cd heart-garden

# 后端
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

- 后端：http://localhost:5000
- 前端：http://localhost:3000

### 配置大模型 (可选)

1. 启动项目后访问 http://localhost:3000/#/settings
2. 找到「AI 对话模式」板块
3. 勾选「启用大模型对话」
4. 填入 API 基础 URL（如 `https://api.deepseek.com/v1`）和 API Key
5. 点击「测试连接」验证配置
6. 点击「保存配置」

## 项目状态

### ✅ v1.0 - MVP 基础版
- 基础日记功能 (CRUD)
- 情绪分析引擎
- AI 对话接口
- 本地数据存储

### ✅ v2.0 - 功能增强版
- 用户系统：注册/登录、JWT 认证、数据隔离
- 多轮对话：上下文感知、对话历史管理
- 统计分析：概览统计、情绪分布
- 自定义词库：用户可扩展情绪词库

### ✅ v2.1 - 前端应用
- Vue 3 前端：手绘风格 UI，完整的前后端分离 SPA
- 8 个功能页面：首页、登录/注册、日记、AI 对话、情绪趋势、统计概览、记忆花园、设置

### ✅ v2.2 - 大模型混合模式 (核心功能)
- **混合模式架构**：规则引擎与大模型双路径共存
- **网页配置界面**：设置页支持 LLM 配置管理
- **OpenAI 兼容接口**：支持 DeepSeek、OpenAI 等任意兼容 API
- **自动降级策略**：大模型失败时自动回退规则引擎
- **Prompt 工程**：规则引擎逻辑转化为 LLM 系统提示词
- **配置持久化**：用户配置保存到数据库
- **连接测试**：一键验证 LLM 配置可用性
- **对话来源标识**：聊天界面显示 AI / 规则标签

### ✅ v2.3 - 安全修复
- DEV_MODE 改为环境变量控制，默认关闭认证跳过
- JWT_SECRET 移除硬编码 fallback，启动时必须配置
- 错误详情仅在开发模式返回，生产环境隐藏内部信息
- SQL 表名迁移增加白名单校验

### ✅ v2.4 - 代码重构
- Auth 接口增加频率限制（注册/登录每 IP 每分钟 5 次）
- 提取 _analyze_with_custom_words() 辅助函数，消除 4 处重复
- 创建 services/constants.py 共享常量，消除模板/表情字典重复
- 移除 20+ 个冗余 try/except（全局 error handler 已兜底）
- 删除 chart.js + vue-chartjs 未使用依赖（~150KB）

### ✅ v2.5 - 功能修复与性能优化
- 修复 AI 陪伴对话历史丢失问题（刷新/切页后对话清空）
- N+1 查询修复：conversations 改用 LEFT JOIN
- stats SQL 合并：7 次查询合并到 3 次
- 新增 GET /api/diaries/:id 端点
- 前端 LLM 超时 15s → 60s
- mood_analyzer 单遍关键词匹配

### ✅ v2.6 - SSE 流式响应
- 新增 /api/chat/stream POST 端点，SSE 事件流
- LLMService.chat_stream 逐 token 流式返回
- ChatPage 改用 fetch ReadableStream 打字机效果

### ✅ v2.7 - 测试覆盖
- mood_analyzer 单元测试（11 个用例）
- prompt_engine 单元测试（6 个用例）
- API 集成测试（16 个用例：auth/diary/stats/mood/conversation）

### ✅ v2.8 - 代码清理
- LLM provider 缓存改为 OrderedDict LRU，最多保留 10 个
- 正常操作日志 info → debug

### ✅ v3.0 - 架构重构
- main.py 1468行 → 27行精简入口
- Flask factory pattern (create_app)
- 模块化拆分：db.py / auth.py / 9个路由模块

### ✅ v3.0.1 - 启动热修复
- 修复 Flask factory 重构后 init_db() 缺少 app context 导致启动崩溃的问题

### ✅ v3.0.2 - 日志系统增强
- setup_logging 增加 stdout StreamHandler，Zeabur/Docker Runtime Logs 可见
- 每个请求生成 X-Request-ID，记录方法、路径、状态码、耗时、用户 ID
- LLM 配置检查、调用结果、流式响应、失败降级原因均进入日志
- 新增日志回归测试，覆盖日志幂等、请求 ID、SSE 流式上下文

### ✅ v3.0.3 - 前端流式调用修复
- 修复 ChatPage 调用 chatStream 但未导入导致的运行时 ReferenceError
- chatStream 增加 HTTP 状态与 ReadableStream body 校验，错误进入浏览器控制台
- 新增前端契约回归测试，防止流式调用导入再次缺失

### ✅ v3.0.4 - 设置页 API Key 保留修复
- 设置页不再把后端脱敏 API Key 绑定到可提交字段，避免掩码覆盖真实密钥
- 保存 LLM 配置时，api_key 缺省或为掩码占位符则沿用数据库已有密钥
- 测试连接未输入新 API Key 时自动使用已保存密钥
- GET/POST LLM 配置响应不回传真实 API Key，仅返回已保存状态与脱敏预览
- 新增 LLM 配置回归测试与设置页前端契约测试

### ✅ v3.0.5 - 情绪判定与统计修复
- AI 陪伴启用大模型时，优先由 LLM 输出结构化情绪判定，失败时回退规则词库
- AI 陪伴普通/流式聊天的用户情绪写入 mood_records，进入情绪趋势与分布统计
- 自定义情绪词库入口暂时关闭，前端不展示/不调用，后端写入接口返回 403
- 扩充规则词库，覆盖“太好了”“太开心”“真好”“完成”等口语化积极表达
- 新增 LLM 情绪解析、聊天统计写入、词库禁用与前端契约回归测试

## API 接口

详见 [SPEC.md](./SPEC.md) 中的 API 接口一览部分。

## 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 函数命名使用 snake_case
- 类命名使用 PascalCase

### 错误处理
- 所有 API 接口统一返回格式
- 异常捕获并记录日志
- 提供友好的错误提示

## 版权说明

Copyright © 2026 Heart Garden Team. All rights reserved.
