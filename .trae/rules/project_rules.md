# Heart Garden - 项目规则

## 文件访问规则

### SPEC.md 文档（关键文件）
- `SPEC.md` 是本项目的技术规格文档，虽然被列在 `.gitignore` 中（不上传 GitHub），但它是项目开发的核心文件
- **AI 助手必须能够正常读取和更新 `SPEC.md` 文件**
- 该文件存放在项目根目录：`e:\AI_Projects\心语花园\SPEC.md`
- `.gitignore` 中的 `SPEC.md` 规则仅用于防止上传到 GitHub，不应影响 AI 工具对该文件的访问

## 项目结构

```
心语花园/
├── app/
│   └── main.py              # Flask 应用主入口
├── services/
│   ├── ai_companion.py      # AI 陪伴服务
│   └── mood_analyzer.py     # 情绪分析服务
├── frontend/                 # Vue 3 + Tailwind 前端
│   ├── src/
│   │   ├── api/             # API 调用封装
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── views/           # 页面组件
│   │   └── App.vue          # 根组件
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── .trae/
│   └── rules/
│       └── project_rules.md  # 本文件 - 项目规则
├── SPEC.md                   # 技术规格文档（.gitignore 排除）
├── README.md                 # 项目说明文档
└── ...其他配置文件
```

## 启动方式

### 后端
```bash
python -m app.main    # http://localhost:5000
```

### 前端
```bash
cd frontend && npm run dev  # http://localhost:3000
```

## 响应语言
- 与用户使用同一种语言交流

## 开发规范
- 遵循 PEP 8 规范
- 函数命名使用 snake_case
- 类命名使用 PascalCase
- 常量使用大写加下划线
- 不添加多余的注释
