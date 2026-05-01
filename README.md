# Heart Garden - 心语花园

## 项目概述

Heart Garden 是一个基于 AI 驱动的情感陪伴应用，旨在为用户提供深度理解、情绪追踪和智能陪伴服务。系统采用本地化部署方案，确保用户数据隐私安全。

## 技术架构

### 后端技术栈

- **Web 框架**: Flask 3.0.0
- **CORS 支持**: flask-cors 4.0.0
- **数据库**: SQLite
- **配置管理**: python-dotenv 1.0.0
- **HTTP 客户端**: requests 2.31.0
- **JWT 认证**: PyJWT 2.8.0
- **日志系统**: Python logging (RotatingFileHandler)

### 服务模块

1. **情绪分析服务** (mood_analyzer.py)
   - 文本情绪识别
   - 关键词提取
   - 情绪趋势分析
   - 自定义词库支持

2. **AI 陪伴服务** (ai_companion.py)
   - 上下文感知对话
   - 多轮对话记忆
   - 个性化回复生成
   - 情感状态维护

## 系统功能

### 核心功能 ✅

1. **用户系统** (v2.0 新增)
   - 用户注册 (POST /api/auth/register)
   - 用户登录 (POST /api/auth/login)
   - 获取用户信息 (GET /api/auth/me)
   - JWT 令牌认证 (7 天有效期)
   - 用户数据隔离

2. **日记记录**
   - 创建日记 (POST /api/diaries)
   - 读取日记列表 (GET /api/diaries)
   - 更新日记 (PUT /api/diaries/:id)
   - 删除日记 (DELETE /api/diaries/:id)
   - 自动时间戳管理
   - 版本更新追踪

3. **情绪分析**
   - 多维度情绪识别
   - 情绪分数计算 (0-100 分制)
   - 情绪标签分类
   - 趋势分析
   - 关键词提取
   - **自定义词库扩展** (v2.0 新增)

4. **智能对话** (v2.0 增强)
   - 上下文感知回复
   - **多轮对话记忆**
   - **对话历史管理**
   - 情感状态适配
   - 个性化交互

5. **数据追踪**
   - 情绪历史记录 (GET /api/mood/trend)
   - 趋势可视化数据
   - 统计分析接口 (GET /api/stats/overview)
   - **情绪分布统计** (GET /api/mood/distribution)

6. **系统功能**
   - 统一错误处理 (400/401/404/500)
   - 日志记录 (RotatingFileHandler)
   - 健康检查接口 (GET /api/health)
   - 环境变量配置

## 数据库设计

### users 表 (v2.0 新增)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | TEXT | 主键，UUID 格式 |
| username | VARCHAR(50) | 用户名，唯一 |
| email | VARCHAR(100) | 邮箱，唯一 |
| password_hash | VARCHAR(255) | bcrypt 密码哈希 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### diaries 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | TEXT | 主键，UUID 格式 |
| user_id | TEXT | 用户 ID，外键 |
| title | TEXT | 日记标题 |
| content | TEXT | 日记正文 |
| mood_score | REAL | 情绪分数 (0-100) |
| mood_label | TEXT | 情绪标签 |
| tags | TEXT | 标签列表 |
| ai_analysis | TEXT | AI 分析结果 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### mood_records 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | TEXT | 主键，UUID 格式 |
| diary_id | TEXT | 关联日记 ID |
| user_id | TEXT | 用户 ID，外键 |
| mood_score | REAL | 情绪分数 |
| mood_label | TEXT | 情绪标签 |
| keywords | TEXT | 情绪关键词 |
| trend | TEXT | 趋势标识 |
| timestamp | TIMESTAMP | 记录时间 |

### conversations 表 (v2.0 新增)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | TEXT | 主键，UUID 格式 |
| user_id | TEXT | 用户 ID，外键 |
| title | TEXT | 对话标题 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### chat_history 表 (v2.0 新增)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | TEXT | 主键，UUID 格式 |
| conversation_id | TEXT | 对话 ID，外键 |
| role | TEXT | 角色 (user/assistant) |
| content | TEXT | 消息内容 |
| mood_label | TEXT | 情绪标签 |
| created_at | TIMESTAMP | 创建时间 |

### custom_words 表 (v2.0 新增)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | TEXT | 主键，UUID 格式 |
| user_id | TEXT | 用户 ID，外键 |
| word | TEXT | 自定义词语 |
| category | TEXT | 词语分类 |
| word_type | TEXT | 类型 (positive/negative) |
| created_at | TIMESTAMP | 创建时间 |

## API 接口规范

### 用户注册

**请求方法**: POST
**请求路径**: /api/auth/register
**Content-Type**: application/json

**请求体**:
```json
{
    "username": "用户名",
    "email": "user@example.com",
    "password": "密码"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "user_id": "uuid",
        "username": "用户名",
        "email": "user@example.com",
        "token": "jwt_token"
    }
}
```

### 用户登录

**请求方法**: POST
**请求路径**: /api/auth/login
**Content-Type**: application/json

**请求体**:
```json
{
    "username": "用户名",
    "email": "user@example.com",
    "password": "密码"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "user_id": "uuid",
        "username": "用户名",
        "email": "user@example.com",
        "token": "jwt_token"
    }
}
```

### 创建日记

**请求方法**: POST
**请求路径**: /api/diaries
**请求头**: Authorization: Bearer \<token\>
**Content-Type**: application/json

**请求体**:
```json
{
    "title": "日记标题",
    "content": "日记内容"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "title": "日记标题",
        "mood_score": 75.5,
        "mood_label": "开心"
    }
}
```

### 获取日记列表

**请求方法**: GET
**请求路径**: /api/diaries
**请求头**: Authorization: Bearer \<token\>
**查询参数**:
- page: 页码 (默认 1)
- per_page: 每页数量 (默认 10)

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total": 100,
        "page": 1,
        "per_page": 10,
        "items": [
            {
                "id": "uuid",
                "title": "日记标题",
                "content": "日记内容",
                "mood_score": 75.5,
                "mood_label": "开心",
                "ai_analysis": "分析结果",
                "created_at": "2026-04-28T22:30:00.000000"
            }
        ]
    }
}
```

### 更新日记

**请求方法**: PUT
**请求路径**: /api/diaries/:id
**请求头**: Authorization: Bearer \<token\>
**Content-Type**: application/json

**请求体**:
```json
{
    "title": "更新后的标题",
    "content": "更新后的内容"
}
```

### 删除日记

**请求方法**: DELETE
**请求路径**: /api/diaries/:id
**请求头**: Authorization: Bearer \<token\>

### 分析文本情绪

**请求方法**: POST
**请求路径**: /api/mood/analyze
**请求头**: Authorization: Bearer \<token\>
**Content-Type**: application/json

**请求体**:
```json
{
    "text": "待分析的文本"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "mood_score": 75.5,
        "mood_label": "开心",
        "keywords": ["开心", "温暖", "幸福"],
        "trend": "上升",
        "positive_count": 5,
        "negative_count": 1
    }
}
```

### 获取情绪趋势

**请求方法**: GET
**请求路径**: /api/mood/trend
**请求头**: Authorization: Bearer \<token\>
**查询参数**:
- days: 天数 (默认 7，最大 90)

### 获取情绪分布

**请求方法**: GET
**请求路径**: /api/mood/distribution
**请求头**: Authorization: Bearer \<token\>
**查询参数**:
- days: 天数 (默认 7，最大 90)

**响应示例**:
```json
{
    "success": true,
    "data": {
        "开心": 45,
        "平静": 30,
        "中性": 20,
        "焦虑": 3,
        "悲伤": 2
    }
}
```

### 获取统计概览

**请求方法**: GET
**请求路径**: /api/stats/overview
**请求头**: Authorization: Bearer \<token\>

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total_diaries": 100,
        "total_mood_records": 150,
        "total_conversations": 20,
        "avg_mood_score": 72.5,
        "most_common_mood": "开心",
        "last_7_days": {
            "avg_score": 75.0,
            "trend": "上升"
        }
    }
}
```

### AI 对话

**请求方法**: POST
**请求路径**: /api/chat
**请求头**: Authorization: Bearer \<token\>
**Content-Type**: application/json

**请求体**:
```json
{
    "message": "用户消息",
    "conversation_id": "对话ID（可选，不传则创建新对话）"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "response": "AI 回复内容",
        "conversation_id": "对话ID",
        "mood": "开心",
        "sentiment": "positive"
    }
}
```

### 对话管理

**创建对话**: POST /api/conversations
**获取对话列表**: GET /api/conversations
**获取对话详情**: GET /api/conversations/:id
**删除对话**: DELETE /api/conversations/:id

### 自定义词库管理

**获取词库**: GET /api/mood/words
**添加词语**: POST /api/mood/words
**删除词语**: DELETE /api/mood/words/:id

**添加词语请求体**:
```json
{
    "word": "振奋",
    "category": "积极",
    "word_type": "positive"
}
```

### 获取记忆花园

**请求方法**: GET
**请求路径**: /api/garden
**请求头**: Authorization: Bearer \<token\>

### 健康检查

**请求方法**: GET
**请求路径**: /api/health

## 情绪分析算法

### 情绪词库

系统内置正负向情绪词库，包括：

**正向情绪**:
- 开心：快乐、高兴、幸福、喜悦、满足、美好、温暖、阳光、灿烂、甜蜜
- 平静：宁静、平和、放松、舒适、安详、自在、悠闲、惬意
- 期待：希望、期待、向往、憧憬、梦想、未来、可能、机会
- 爱：爱、喜欢、珍惜、在乎、关心、思念、牵挂、温柔
- 感激：感谢、谢谢、感恩、感动、温暖、幸福、幸运

**负向情绪**:
- 焦虑：担心、害怕、恐惧、紧张、不安、压力、负担、沉重
- 悲伤：难过、伤心、失落、失望、痛苦、绝望、孤独、寂寞
- 愤怒：生气、愤怒、烦躁、恼火、不满、讨厌、不爽
- 疲惫：累、困、无力、厌倦、疲惫、崩溃

### 情绪分数计算

```
情绪分数 = (正向词数 / (正向词数 + 负向词数)) * 100

平滑处理:
情绪分数 = max(20, min(80, 计算结果))
```

### 情绪标签分类

| 分数区间 | 情绪标签 |
|----------|----------|
| [75, 100] | 开心 |
| [60, 75) | 平静 |
| [40, 60) | 中性 |
| [25, 40) | 焦虑 |
| [0, 25) | 悲伤 |

### 趋势判断逻辑

```
正向词数 > 负向词数 + 2: 上升
负向词数 > 正向词数 + 2: 下降
否则: 平稳
```

## 部署说明

### 环境要求

- Python 3.9+
- SQLite 3.8+
- Docker (可选)

### 本地部署

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env 文件，设置必要配置
```

4. 运行应用
```bash
python -m app.main
```

### Docker 部署

```bash
docker build -t heart-garden .
docker run -p 5000:5000 heart-garden
```

## 开发规范

### 代码风格

- 遵循 PEP 8 规范
- 函数命名使用 snake_case
- 类命名使用 PascalCase
- 常量使用大写加下划线

### 错误处理

- 所有 API 接口统一返回格式
- 异常捕获并记录日志
- 提供友好的错误提示

### 日志规范

```python
import logging

logger = logging.getLogger(__name__)

logger.info("操作成功")
logger.warning("操作警告")
logger.error("操作失败")
logger.exception("异常信息")
```

## 项目状态

### v1.0 - MVP 基础版 ✅

- 基础日记功能 (CRUD)
- 情绪分析引擎
- AI 对话接口
- 本地数据存储
- 统一错误处理
- 日志记录系统
- 环境变量配置

### v2.0 - 功能增强版 ✅

- **用户系统**: 注册/登录、JWT 认证、数据隔离
- **多轮对话**: 上下文感知、对话历史管理
- **统计分析**: 概览统计、情绪分布
- **自定义词库**: 用户可扩展情绪词库
- **UUID 主键**: 所有数据表使用 UUID

### v2.1 - 规划中 📋

- 语音日记功能
- AI 回复风格个性化
- 高级情绪分析
- 单元测试覆盖

## 版权说明

Copyright © 2026 Heart Garden Team. All rights reserved.
