简体中文 | [English](README.en.md)

# 心语花园 · Heart Garden

**本地优先的个人心情日记与双模情感陪伴智能体**。

`Heart Garden` 是一款注重隐私安全与情绪共情的本地优先（Local-First）情感记录与陪伴系统。它将日记记录、情感评分、趋势洞察与对话陪伴有机融合，采用“本地规则引擎 + 外部可选大语言模型”的双模混合架构：在无网络或未配置大模型时，基于本地情感词典与规则引擎离线运行；在启用大语言模型时，提供富有温度的深度多轮共情对话，并在模型调用受阻时无缝回退，确保任何时候都能提供稳定的情感守候。

---

## 核心特性

* **本地优先与数据私密（Privacy-First）**：所有用户日记、情感流变轨迹与个性化设定均保存在本地 SQLite 数据库中；API Key 严格掩码加密存储，杜绝敏感生活记录上云泄露。
* **双模混合对话引擎（Hybrid Companion Engine）**：
  * **离线规则引擎**：开箱即用，基于内置心理学关怀词典与模式匹配算法，零外部依赖，极速响应。
  * **LLM 深度共情模式**：支持任意 OpenAI 兼容接口（如 GPT、DeepSeek、Claude 等），提供高情商多轮长上下文共鸣。
  * **无感平滑回退**：若大模型遭遇网络中断或额度耗尽，对话系统自动无缝降级至本地规则引擎，界面明确标注回复来源。
* **情绪量化与多维图表**：对日记文本执行情绪评分、正负向极性分析与情感标签提取，提供周度/月度情绪雷达与趋势折线图。
* **关怀提醒与防打扰机制**：具备连续低落情绪温情预警、每日关怀推送与周度情绪复盘报告，内建免打扰时段控制。
* **用户隔离与鉴权**：完备的 JWT 用户身份认证体系，支持单机多用户数据严格隔离。

---

## 架构与项目结构

```text
heart-garden/
├── app/                  # Flask 后端服务
│   ├── main.py           # 后端入口与路由注册
│   ├── models/           # SQLite 数据库模型（用户、日记、情绪、配置）
│   ├── services/         # 混合对话调度、情绪分析引擎、提醒服务
│   └── utils/            # JWT 鉴权与安全校验
├── frontend/             # 前端单页面应用（React + Vite）
│   ├── src/              # 页面（日记书写、情绪看板、伴侣对话、设置）
│   └── package.json
├── requirements.txt      # Python 依赖清单
└── start.bat             # Windows 一键启动脚本
```

---

## 快速开始

### 环境依赖
* **Python**：3.9 或更高版本
* **Node.js**：18 或更高版本
* **数据库**：SQLite 3.8+（Python 内置）

### 运行方式

#### 1. Windows 一键启动
直接双击根目录下的 `start.bat` 即可同时启动前后端服务。

#### 2. 手动启动
```bash
# 终端 1：启动后端服务
python -m venv venv
# Windows 激活：
venv\Scripts\Activate.ps1
# macOS/Linux 激活：
# source venv/bin/activate

pip install -r requirements.txt
python -m app.main

# 终端 2：启动前端应用
cd frontend
npm install
npm run dev
```

启动完成后，前端默认运行在 `http://localhost:3001`，后端接口运行在 `http://localhost:5000`。

---

## 配置与大模型接入

1. 系统默认以离线规则模式运行，无需任何初始配置。
2. 如需开启 LLM 陪伴，打开前端右上角 **设置** 页面：
   * 勾选 **启用 LLM 对话**；
   * 填入 OpenAI 兼容的 Base URL、模型名称与 API Key；
   * 点击 **测试连接**，验证通过后点击 **保存配置**。
3. 系统在持久化存储 API Key 时自动脱敏遮罩，前端请求绝不回传明文凭据。

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
