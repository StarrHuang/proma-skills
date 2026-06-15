# 路径与工作区初始化

> 本 skill 设计为**可复用**：不在文档中写死任何用户本机路径。所有路径通过「工作区 + 配置文件」解析。

## 典型目录布局

```
{SIF_WORKSPACE}/                 ← 工作区根目录（含 .sif-config.json）
├── .sif-config.json             ← 用户本地配置（勿提交 git）
├── .sif-config.example.json     ← 模板（可提交）
├── sif-keyword-scout/           ← Skill 1
├── sif-keyword-tracker/         ← Skill 2
└── web-access/                  ← 浏览器自动化（可选，方式 B 需要）
```

Skills 可安装到 `~/.agents/skills/`（目录联接/junction 指向上述目录），**配置文件始终在工作区根目录**，与 skill 安装位置解耦。

## 首次使用：Agent 必须执行的初始化

> **完整对话脚本** → [`first-time-setup.md`](first-time-setup.md)（output_dir 必问、禁止填他人路径）

### 1. 解析工作区

```powershell
python "{SKILL_SCOUT}/scripts/resolve_workspace.py"
```

返回 JSON。关注字段：

| 字段 | 含义 |
|------|------|
| `workspace_found` | false → 需引导用户指定工作区或复制 example 配置 |
| `needs_output_dir` | true → 询问用户输出根目录（只问一次） |
| `needs_download_dir` | true → 仅在「方式 B 浏览器导出」时需要 |
| `scripts.*` | 后续 Python 命令应使用此处返回的绝对路径 |

写入配置：

```powershell
python "{SKILL_SCOUT}/scripts/resolve_workspace.py" --init-output-dir "用户指定的输出目录"
python "{SKILL_SCOUT}/scripts/resolve_workspace.py" --init-download-dir "用户浏览器下载目录"
```

也可设置环境变量 `SIF_WORKSPACE` 指向工作区根目录。

### 2. 下载目录探索（方式 B，首次）

若 `download_dir` 为空，按优先级：

1. **询问用户**：「你的 Chrome/Edge 默认下载文件夹路径是？」
2. **AI 探索**（web-access CDP）：
   ```javascript
   // 在浏览器 eval
   // chrome://settings/downloads 或检查最近下载文件所在目录
   ```
3. **常见候选**（Windows）：
   - `%USERPROFILE%\Downloads`
   - `D:\下载`（部分中文系统用户自定义）
4. 确认后写入 `--init-download-dir`

### 3. web-access 路径

- 读取 `{WEB_ACCESS}/SKILL.md`（路径来自 `resolve_workspace.py` 输出）
- 若 `web-access` 目录不存在 → 方式 B 不可用，改走方式 A 手动导出
- **来源**：第三方 Skill，上游 [github.com/eze-is/web-access](https://github.com/eze-is/web-access)，作者一泽 Eze（MIT）；详见 `web-access/README.md`

## 配置文件字段

```json
{
  "output_dir": "",
  "download_dir": "",
  "sif_url": "https://www.sif.com/skill/keywords-library?country=US"
}
```

| 字段 | 何时询问 | 说明 |
|------|---------|------|
| `output_dir` | 首次必问 | 所有 ASIN 报告的根目录 |
| `download_dir` | 方式 B 首次 | 浏览器下载后 Agent 从此处复制文件 |
| `sif_url` | 可选 | 默认 US 关键词库入口 |

## 本次运行目录结构（按日期）

先执行 `ingest_raw.py`（无文件时仅建目录；有路径时自动复制重命名）：

```
{output_dir}/{ASIN}/{DATE}/
├── 原始数据/
│   ├── 关键词调研_{DATE}.xlsx
│   ├── 反查流量词_{DATE}.xlsx
│   └── 查广告词_{DATE}.xlsx
└── 处理结果/
    └── 仅 xlsx / docx（json、insights、charts 在 Word 生成后自动删除）
```

`ASIN历史记录.xlsx` 记录跑库时刻（含时分）与路径 `{ASIN}/{DATE}`。

## 禁止事项

- 不要在 skill 文档、示例命令中写死 `D:\Example\...` 等发布者个人路径
- 不要假设 Downloads 在固定位置
- 命令中的 `{SKILL_SCOUT}`、`{OUTPUT_DIR}` 等占位符，执行前必须用 `resolve_workspace.py` 或配置值替换
