# Sif 浏览器导出 SOP（方式 B：AI 自动化）

> 前置：已读取 **web-access** skill，Chrome/Edge CDP 可用，Sif 已在浏览器登录。  
> 路径：先运行 `resolve_workspace.py`，使用返回的 `web_access`、`download_dir`、`output_dir`。

---

## 通用前置

1. 初始化 CDP：`node "{WEB_ACCESS}/scripts/check-deps.mjs" --browser chrome`  
2. 关闭弹窗：点击 `我知道了`（可能有多个）  
3. 若 `download_dir` 为空 → 见 [`path-setup.md`](path-setup.md) 探索或询问用户  
4. 下载后：从 `{download_dir}` 取**最新**文件 → 复制重命名到 `{output_dir}/{ASIN}/{DATE}/原始数据/`

---

## 表1：关键词调研（8 步向导）

**URL：** `https://www.sif.com/skill/keywords-library?country=US`

| 步骤 | 操作 | 选择器/说明 |
|------|------|------------|
| 1 | 输入 ASIN | `input[type=text]` → 填 ASIN → 触发 `input` |
| 2 | 开始调研 | 点击 `.search-btn` |
| 3 | Step1 全选 | 表头 checkbox 全选 → `确认选中的 N 个关键词` |
| 4 | Step3 确认竞品 | `确认竞品并继续（N）` |
| 5 | Step5 相关性 | 默认滑块 → `确认并继续` |
| 6 | Step6-7 | 等待拓词+竞价（约 15–30 秒） |
| 7 | Step8 下载 | `.download-card button` 或文本 `下载` |

**保存为：** `关键词调研_{DATE}.xlsx`  
**Sif 原始名：** `Sif关键词调研-US-{ASIN}-*.xlsx`

---

## 表2：反查流量词

**URL：** `https://www.sif.com/reverse`

| 步骤 | 操作 | 选择器/说明 |
|------|------|------------|
| 1 | 关教程 | `我知道了` |
| 2 | 输入 ASIN | `input[placeholder*="ASIN"]` |
| 3 | 反查 | 文本含 `反查流量词` 的绿色按钮 |
| 4 | 等待 | 出现 `当前筛选：最近7天的全部流量词，数量N` |
| 5 | 定位工具栏 | 滚动到 `流量词` / `筛查相关性并加入词库` / `批量操作` |
| 6 | **下载** | **第 2 个按钮**：`.downloadPolorBtn.noMargin:not(.compareDownload)` |

**保存为：** `反查流量词_{DATE}.xlsx`  
**Sif 原始名：** `asinKeywords_{ASIN}_*.xlsx`

> ⚠️ 不是页面最底部导出；是流量词表格工具栏第 2 个下载图标。

---

## 表3：查广告词

**URL：** `https://www.sif.com/adxray-searchterm?country=US`

| 步骤 | 操作 | 选择器/说明 |
|------|------|------------|
| 1 | 关教程 | `我知道了` |
| 2 | 输入 ASIN | `input[placeholder*="ASIN"]` |
| 3 | 查询 | 文本 `查广告词` |
| 4 | 等待 | SP 表格 + `下载数据` 按钮出现 |
| 5 | 下载 | `button.el-button--primary` 文本 `下载数据` |

**保存为：** `查广告词_{DATE}.xlsx`  
**Sif 原始名：** `asinAdKwView_{ASIN}_*.xlsx`

---

## 已知陷阱

- 未登录可开页但无法导出 → 请用户在浏览器登录 Sif 后继续  
- 表1 为**合并 Sheet**（`高、中、低相关（N个）`），表头在第 1 行 → 见 [`table-schema.md`](table-schema.md)  
- 表2/表3 表头在第 2 行（第 1 行元信息）  
- 多次下载会产生 `(1)(2)` 后缀，取最新时间戳  
- 下载目录因用户而异，**必须**写入 `.sif-config.json` 的 `download_dir`，勿写死任何本机路径

---

## 导出完成后

对照 [`table-schema.md`](table-schema.md) 校验三张文件，再进入 Python 处理流程。
