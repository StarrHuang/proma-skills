---
name: harness-memory
description: Harness 左/右脑双模记忆系统。基于 DeepSeek MLA 稀疏注意力和大脑左右半球分工理念，提供 BM25+向量混合检索和视觉化上下文压缩。当用户提到 compress-to-visual、route-context、update-memory、render-dashboard、记忆压缩、上下文路由、更新记忆、渲染仪表盘时使用。
---

# Harness Memory — 左/右脑双模记忆

## Overview

基于 DeepSeek MLA 稀疏注意力、大脑左右半球分工、Tesla BEV 架构理念的 Agent 记忆系统。左右脑分区存储，视觉化上下文压缩，BM25+向量混合检索。

触发任一指令时，首先检视 `~/.proma/memory/corpus-callosum.json` 路由表，按匹配权重加载相关左右脑片段。

## 四个工具

### 1. compress-to-visual

```
/compress-to-visual <sessionId?>

将指定会话（或当前会话）对话历史压缩为 HTML 知识图谱：
1. 从 ~/.proma/memory/left/decisions.jsonl 提取关键决策
2. 生成 Obsidian 风格的交互式 HTML 图谱 (节点+边+颜色编码)
3. 保存到 ~/.proma/memory/right/context-map.html
4. 同时在 ~/.proma/memory/right/snapshots/ 保存 PNG 快照
```

### 2. route-context

```
/route-context <query>

检索左右脑相关上下文：
1. BM25 关键词 + 向量余弦相似度 + 图谱遍历 RRF 融合
2. 从 left/decisions.jsonl, left/facts.jsonl, left/patterns.json 检索
3. 加载 right/context-map.html (如果存在)
4. 返回组装好的 system prompt 注入文本
```

### 3. update-memory

```
/update-memory

从当前对话中提取关键信息并更新左右脑：
1. 提取决策 → left/decisions.jsonl
2. 提取事实 → left/facts.jsonl  
3. 更新向量索引 → index/vectors.json
4. 更新 BM25 索引 → index/bm25.json
5. 更新知识图谱 → index/graph.json
6. 更新路由表 → corpus-callosum.json
```

### 4. render-dashboard

```
/render-dashboard <projectName>

生成项目状态仪表盘 HTML：
1. 从 left/decisions.jsonl 统计该项目的决策热力图
2. 从 facts.jsonl 提取项目相关事实
3. 生成 Grid 布局的仪表盘 HTML
4. 保存到 ~/.proma/memory/right/dashboards/{project}.html
```

## 配置

配置文件：`~/.proma/memory/harness.config.json`

```json
{
  "enabled": true,
  "threshold": 10,
  "maxContextTokens": 4000,
  "decayDays": 30
}
```

- `threshold`: 超过此轮数自动触发压缩
- `maxContextTokens`: 每次注入的最大上下文 token 数
- `decayDays`: Ebbinghaus 遗忘曲线衰减天数

## 存储结构

```
~/.proma/memory/
├── left/        ↔ 左脑（结构化文本 — decisions/facts/patterns/sessions）
├── right/       ↔ 右脑（视觉空间 — HTML图谱/仪表盘/PNG快照）
├── index/       ↔ 索引层（向量/BM25/图谱）
├── corpus-callosum.json ↔ 路由表
└── harness.config.json   ↔ 配置
```
