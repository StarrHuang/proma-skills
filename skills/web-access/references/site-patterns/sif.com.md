---
domain: sif.com
aliases: [Sif, Sif关键词, 关键词调研]
updated: 2026-06-11
---
## 平台特征

- 亚马逊关键词 SaaS，需登录态
- 默认 US：`https://www.sif.com/skill/keywords-library?country=US`
- 三张表入口：
  - 表1：`/skill/keywords-library?country=US` → 8 步向导 → Step8 `.download-card button`
  - 表2：`/reverse` → 工具栏 `.downloadPolorBtn.noMargin:not(.compareDownload)`（第 2 个下载图标）
  - 表3：`/adxray-searchterm?country=US` → `button.el-button--primary` 文本「下载数据」

## 有效模式

- `find-url.mjs sif 关键词` 从历史定位入口
- 登录态来自用户 Chrome/Edge CDP
- **下载目录因用户而异**：写入工作区 `.sif-config.json` 的 `download_dir`，不要假设 Downloads 路径

## 数据获取方式（sif-keyword-scout）

| 方式 | 说明 |
|------|------|
| A 手动 | 给用户 URL + 按钮指引，用户自行下载（更快） |
| B CDP | Agent 按 browser-export-sop 点击，从 `download_dir` 取文件 |

## 表结构（处理脚本依赖）

- 表1：合并 Sheet 或 高/中/低 三 Sheet → 见 sif-keyword-scout `references/table-schema.md`
- 表2/表3：第 1 行元信息，**第 2 行表头**
- F 列 ABA 排名 ≠ 搜索量

## 已知陷阱

- 未登录无法导出
- 表1 已从「一键下载」改为 8 步向导
- 表2 下载在工具栏，不是页面底部
