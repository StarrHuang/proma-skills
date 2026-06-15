# 门槛参数说明（标品 / 非标品）

> **不要改脚本里的数字。** 用 `--product-type` 选预设，暂停点用 CLI 覆盖单项。

## 快速用法

```powershell
# 默认非标品（沙发套、定制类、小类目）
python process_table1.py --mode compute-thresholds --input "..." --product-type 非标品

# 标品（标准 SKU、竞争集中）
python process_table1.py --mode process ... --product-type 标品 --stage 新品期

# 暂停点① 用户要求放宽 S 级集中度
python process_table1.py --mode process ... --product-type 非标品 --s-conc-max 0.30

# 暂停点② 小类目缺口词太少
python process_table3.py ... --product-type 非标品 --sv-threshold 1000
```

Agent 跑前简报应问：**标品还是非标品？** 写入 `ingest_raw --product-type` 和后续三条 `process_*`。

`.sif-config.json` 可设 `"default_product_type": "非标品"`，Agent 未指定时采用。

---

## 预设对照

| 参数 | 标品 | 非标品 | CLI 覆盖 |
|------|------|--------|----------|
| S 级集中度上限 | 0.30 | 0.25 | `--s-conc-max` |
| A 级集中度上限 | 0.35 | 0.35 | `--a-conc-max` |
| S/A 搜索量门槛 | **自动分位数 97/85** | 同左 | `--s-threshold` / `--a-threshold` |
| B 级要求转化率 | 新品期放宽 | 新品期放宽 | （随 stage） |
| 表2 高机会集中度 | 0.45 | 0.40 | `--t2-opp-conc-max` |
| 表2 纯广告自然占比 | <20% | <20% | `--t2-pure-ad-nat-max` |
| 表3 缺口搜索量下限 | 3000 | 2000 | `--sv-threshold`（0=用预设） |
| 表3 缺口份额上限 | 5% | 5% | `--gap-share-max` |
| 表3 防守份额下限 | 20% | 20% | `--defense-share-min` |

---

## S≥5946、A≥1114 是什么？为什么 S 级只有 2 个？

**这两个数字不是预设里的固定值**，而是每次跑表1时，对「高相关词」周搜索量做 **97 / 85 分位数** 算出来的（B08 6.12 数据示例：S=5946，A=1114）。

S 级还要**同时**满足（非标品预设）：

1. 相关性 = 高相关  
2. 周搜索量 ≥ S 门槛（5946）  
3. 建议竞价 < 中位数 × 1.2  
4. **Top3 集中度 < 0.25**（非标品比标品 0.30 更严）

因此：大词搜索量够，但集中度 ≥0.25 会被压到 A 级或带降级理由——**S 仅 2 个通常是数据信号，不是脚本算错**。暂停点①可试：

- `--s-conc-max 0.30`（放宽 S 集中度）  
- 或 `--product-type 标品`（标品默认 S 集中度 0.30）  
- 若仍嫌 S 门槛过高：`--s-threshold 4000`（手动覆盖分位数）

---

## 行业做法对照（公开资料，无统一「5946」标准）

| 维度 | 常见做法 | 本 Skills |
|------|----------|-----------|
| 标品 | 用 Sif 默认相关性；竞品池大；新品期可收紧高相关 | `s_conc_max=0.30`，表3 `sv_threshold=3000` |
| 非标品 | **自定义相关性**、小竞品池（约 35–50 ASIN）、缺口搜索量按体量 2000–5000 | `s_conc_max=0.25`，表3 `sv_threshold=2000` |
| 搜索量分层 | 各卖家按词库分位数或绝对值自定，**无行业统一 S/A 数字** | 97/85 分位数自动化，可用 CLI 覆盖 |
| 缺口/防守 | 份额阈值因类目差异大 | 缺口 <5%、防守 >20%，暂停点②可调 |

参考：Sif 官方教程强调「高/中/低相关 + 搜索量/集中度/转化」组合筛选，而非固定搜索量门槛。

---

## 何时改什么

| 现象 | 建议 |
|------|------|
| 大词全在 A 级、S 级≤2 | `--s-conc-max 0.30` 或改 `--product-type 标品` |
| B 级词极少 | 已是新品期放宽；可确认 `--stage 新品期` |
| 高机会词过少 | `--t2-opp-conc-max 0.5` |
| 缺口词 0~3 个 | `--sv-threshold 1000` 或 `--gap-share-max 8` |
| 防守词永远 0 | 先查份额列是否为本店；再试 `--defense-share-min 15` |

完整 Agent 引导见 `amazon-expert-guide.md` 暂停点 ①②。
