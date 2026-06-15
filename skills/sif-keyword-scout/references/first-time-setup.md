# 首次使用引导（Agent 必读）

> **原则**：`.sif-config.json` 里的路径是**每个用户自己**填的，skill 文档和脚本里**没有**也不应出现发布者的个人路径（如 `D:\Example\...`）。  
> Agent 第一次帮用户跑 ASIN 时，必须先完成本引导，再执行 `ingest_raw` 或处理脚本。

---

## Agent 首次对话脚本（按顺序）

### 第 1 步：确认工作区

运行 `resolve_workspace.py`。若 `workspace_found: false`：

```
还没找到 Sif 工作区配置。请告诉我：
1. 你解压/克隆 skills 的文件夹路径（应包含 sif-keyword-scout 和 .sif-config.example.json）
或
2. 我帮你在该目录复制一份 .sif-config.json 模板
```

典型布局（**用户的**目录，不是示例路径）：

```
{用户解压的 sif-skills 文件夹}/
├── .sif-config.json          ← 本地配置，每人不同
├── sif-keyword-scout/
├── sif-keyword-tracker/
└── web-access/               ← 可选
```

也可设置环境变量 `SIF_WORKSPACE` 指向上述根目录。

---

### 第 2 步：配置输出目录（必问，只问一次）

当 `needs_output_dir: true` 时，**必须**先问用户，**禁止**擅自填路径：

```
请指定「报告输出根目录」——之后所有 ASIN 的分析结果都会保存在这里。

建议：
• 选一个空间充足的磁盘（如 D:\SifReports 或 ~/Documents/Sif关键词）
• 目录可以不存在，脚本会自动创建
• 结构会是：{你选的目录}/{ASIN}/{日期}/原始数据 + 处理结果

请直接发完整路径（例如 D:\MyWork\SifOutput）
```

用户回复后写入：

```powershell
python "{scripts.resolve_workspace 同目录}/resolve_workspace.py" --init-output-dir "用户发的路径"
```

**验证**：再跑一次 `resolve_workspace.py`，确认 `needs_output_dir: false`，并向用户复述：

```
已保存输出目录：{output_dir}
之后跑 ASIN 都会写到这里，除非你说要改。
```

---

### 第 3 步：下载目录（仅方式 B 需要）

当用户选择「Agent 帮我在浏览器下载 Sif 表」且 `needs_download_dir: true`：

```
你平时浏览器下载文件保存在哪个文件夹？
常见：C:\Users\你的用户名\Downloads  或  D:\下载
```

写入 `--init-download-dir`。若用户只用**方式 A（手动导出）**或**方式 C（直接给 xlsx 路径）**，可跳过，并说明：

```
未配置 download_dir 不影响手动导出；只有 Agent 自动从浏览器复制文件时才需要。
```

---

### 第 4 步：Skills 安装（若 Agent 找不到 skill）

若用户刚解压包、Cursor 未识别 skill：

```
请把 sif-keyword-scout / sif-keyword-tracker 联接或复制到：
  Windows: %USERPROFILE%\.agents\skills\
  然后重启 Cursor
详见工作区 README.md
```

---

### 第 5 步：跑前简报（每次 ASIN 必做）

配置就绪后，在跑第一个 ASIN 前仍要确认 ASIN、阶段、类目（见 `amazon-expert-guide.md` 跑前简报）。

---

## 配置文件说明（给用户看的摘要）

| 字段 | 谁填 | 何时问 | 示例 |
|------|------|--------|------|
| `output_dir` | **用户** | 首次必问 | `D:\SifReports` |
| `download_dir` | **用户** | 仅方式 B 首次 | `C:\Users\xxx\Downloads` |
| `sif_url` | 一般默认 | 很少改 | US 关键词库 URL |

**不要**把发布者测试目录写进用户配置。打包分发时只带 `.sif-config.example.json`（字段为空字符串）。

---

## 修改已有配置

用户说「换个输出目录」：

```powershell
python resolve_workspace.py --init-output-dir "新路径"
```

历史记录 `ASIN历史记录.xlsx` 仍在**旧 output_dir** 下；换目录后相当于新工作区，需说明「历史不会自动迁移，除非手动复制该 xlsx」。

---

## 禁止事项（Agent）

- ❌ 使用 skill 文档或对话里出现的**他人**路径作为默认值  
- ❌ 未询问就把 `output_dir` 写成 Agent 本机路径  
- ❌ 假设 Downloads 在固定位置  
- ❌ 配置未完成就 `ingest_raw` / `process`
