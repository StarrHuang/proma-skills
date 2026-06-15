# 方式 A：用户手动导出（推荐，速度更快）

> 适合：已熟悉 Sif、希望 5 分钟内完成导出、或不想开浏览器自动化的用户。  
> Agent 收到文件后直接进入 Step 5 处理，**跳过 web-access**。

## 你需要准备的三张表

| # | Sif 功能 | 保存文件名（Agent 要求） | Sif 原始文件名特征 |
|---|---------|------------------------|-------------------|
| 1 | 关键词调研 | `关键词调研_{DATE}.xlsx` | `Sif关键词调研-US-{ASIN}-*.xlsx` |
| 2 | 反查流量词 | `反查流量词_{DATE}.xlsx` | `asinKeywords_{ASIN}_*.xlsx` |
| 3 | 查广告词 | `查广告词_{DATE}.xlsx` | `asinAdKwView_{ASIN}_*.xlsx` |

`DATE` = 当天 `YYYYMMDD`，例如 `20260611`。

## 快速操作指引（给用户看的）

### 表1 关键词调研

1. 打开：https://www.sif.com/skill/keywords-library?country=US  
2. 输入 ASIN → 点「开始调研」  
3. 按向导逐步：**全选核心词 → 确认竞品 → 确认并继续**（相关性滑块默认即可）  
4. 最后一步点 **「下载」**  
5. 将文件交给 Agent（**不必手动重命名**）：
   - 直接发三个文件路径，或
   - 放入任意文件夹后告诉 Agent 路径  
   Agent 会运行 `ingest_raw.py` 自动识别并复制到 `{output_dir}/{ASIN}/{DATE}/原始数据/`

### 表2 反查流量词

1. 打开：https://www.sif.com/reverse  
2. 输入 ASIN → **反查流量词**  
3. 等到出现「当前筛选：最近7天的全部流量词」  
4. 在表格上方工具栏（流量词 / 筛查相关性 / 批量操作 那一行），点 **第 2 个下载图标**（不是页面最底部）  
5. 保存为 `反查流量词_{DATE}.xlsx`

### 表3 查广告词

1. 打开：https://www.sif.com/adxray-searchterm?country=US  
2. 输入 ASIN → **查广告词**  
3. 等表格加载完 → 点右上角 **「下载数据」**  
4. 保存为 `查广告词_{DATE}.xlsx`

## Agent 接收方式

用户可任选其一：

1. **直接放到目录**：告知 Agent「文件已在 `{output_dir}/{ASIN}/{DATE}/原始数据/`」  
2. **拖拽/粘贴路径**：Agent 复制到标准目录并重命名  
3. **分步提供**：缺哪张补哪张，Agent 校验三张齐全后再处理

## 文件校验（Agent 执行）

```powershell
# 检查三张表是否齐全
python -c "
import os, sys
root = r'{output_dir}/{ASIN}/{DATE}/原始数据'
need = ['关键词调研_{DATE}.xlsx','反查流量词_{DATE}.xlsx','查广告词_{DATE}.xlsx']
missing = [f for f in need if not os.path.isfile(os.path.join(root, f))]
print('缺失:', missing if missing else '三张表齐全')
sys.exit(1 if missing else 0)
"
```

缺文件时列出上表操作指引，**不要**强行进入 Python 处理。

## 与方式 B 的关系

- 方式 A 不需要 `download_dir` 配置  
- 表结构要求与方式 B 完全相同 → 见 [`table-schema.md`](table-schema.md)
