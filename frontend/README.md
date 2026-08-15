# TradingAgents 前端（docs/vue-frontend.md M1）

暗色金融终端风格的 Vue 3 单页应用：浏览交易分析报告树、每日研报总结、板块轮动报告、矛盾追踪（v3.3）、决策日志与配置。

## 运行

```bash
# 1. 后端（TradingAgent conda 环境，已含 fastapi/uvicorn）
python -m uvicorn webapi.main:app --port 8000

# 2. 前端（需要 Node 18+，首次）
cd frontend
npm install
npm run dev          # http://localhost:5173（/api 自动代理到 8000）
```

生产构建：`npm run build`（产物在 `frontend/dist/`）。

## 结构

```
frontend/src/
├── App.vue                 # 侧边导航 + 顶栏 + 路由
├── styles/main.css         # 设计系统（docs 5.0 tokens）
├── api/                    # 类型 + fetch 封装
├── stores/contradictions.ts# 矛盾筛选状态
├── views/                  # 8 个页面（任务中心为 M2 占位）
└── components/             # MarkdownViewer / DirectionBadge / 抽屉等
```

## 与设计文档的差异（ponytail）

- 文档技术栈列了 **Element Plus**；本实现组件全部自写（表格/抽屉/徽章），样式严格按 5.0 设计 tokens，未引入 Element Plus 依赖——页面视觉更贴合设计系统。如后续需要复杂表单/虚拟滚动，再引入并只替换对应组件。
- `npm run build` 不跑 `vue-tsc` 类型门禁，仅 `vite build`；升级路径：需要时把 `build` 改为 `vue-tsc -b && vite build`。
