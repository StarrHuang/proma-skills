---
name: metabase-card-review
version: 1.0.0
description: >
  Metabase 看板优化端到端工作流 — 拉取SQL→数据库实测→找bug/口径错误→多轮改写→美化（列压缩≤11/emoji颜色状态码/行级染色）→提交冒烟→沉淀笔记。

  触发词: review看板、优化看板SQL、检查dashboard bug、改进Card、
  美化看板、美化表格、metabase beautify、列压缩、加色带、加emoji。
---

# Metabase 看板 / Card Review & 优化工作流

把"review + 优化 Metabase 看板"做成可重复、不漏步的流程。核心是**绝不轻信 SQL 字面意思，所有假设都用数据库实测验证**。

## 何时触发

- 用户说"review 看板"、"看看这个 dashboard 有没有问题"、"优化这张 card"
- 用户贴 `metabase.<host>/dashboard/<id>` 或 `metabase.<host>/question/<id>` 链接要求审查
- 用户报告"这个数字不对"、"这个列没意义"、"卡片排序错了"
- 用户在已经做完一轮后说"还有 X 列也要改"——直接进入第 4 步开始新一轮迭代

## 前置依赖

- Metabase MCP 已配置（`mcp__metabase__*` 工具可用），或有 `METABASE_API_KEY` 环境变量可走 curl/Python
- 数据库直连或 Metabase MCP 的 `metabase_query` 工具可用于实测验证
- 工作区有 `note.md` 用于沉淀（路径见 references/sop.md）

---

## 标准 6 步流程

### Step 1 — 定位 & 全量拉取

明确目标看板/card ID。**不要靠搜索关键词去猜**，让用户给 URL 或 ID。

拉取范围：
- 看板：`metabase_dashboard(dashboard_id)` 拿到所有 dashcards 列表
- 每张 card：`GET /api/card/<id>` 拿到 dataset_query.native.query（这才是真 SQL）
- 把所有 SQL 落到本地 `/tmp/<scope>/card_<id>.sql`，便于 diff 和回滚

**绝不**靠 metabase_card（query 接口）反推 SQL——它只返回数据，不返回查询。

详细命令见 `references/sop.md` §拉取 SQL。

### Step 2 — 字段语义验证（最关键的一步）

**SQL 写什么 ≠ 字段就是什么意思**。逐张 card 找出每个非平凡字段，去数据库验证语义：

- 字段注释（`col_description`）
- 字段在不同分支/分组下的取值分布
- 字段间的数学关系（A = B + C 是否成立？）
- 字段唯一性（一对一还是一对多？）

典型陷阱（已验证踩过的坑，详见 `references/known-pitfalls.md`）：
- **fulfillment_channel='ALL' vs FBA+FBM**：'ALL' 是预聚合行，不能再 join FBA/FBM 否则×3
- **shipment_on_way_total ≠ f7+f14+f21**：total 包含所有时效，并列展示会被误解为加总
- **MAX(tier) 取字符串**：依赖 Unicode 序，'爆品' 不一定最大，**改用 SUM(ds) 重新分层**
- **NULLIF 在边界值返回 NULL**：会污染下游 GREATEST/ABS 比较，改用 GREATEST(1, ...)
- **当前快照 vs 历史趋势**：`amazon_fba_stock` 是快照（无历史），`amazon_product_performance_statement.fba_sale_stock` 才能做趋势
- **suggest_num vs review_num**：采购单的 suggest_num 已被跟单分拆，原始批量在 purchase_plan_sku.review_num

### Step 3 — Review 报告（Musk 五步法）

输出结构化报告：
1. **致命问题（必须改）**：漏算/双计/口径错误，直接影响决策
2. **口径不一致**：同一指标多种算法并存
3. **冗余/可删**：柱状/汇总卡是否有列表卡的子集
4. **Musk 五步法**：合理性 → 删 → 简 → 加速 → 自动化
5. **ROI 排序**：每条改动给出工时估计 + 影响范围

报告写到工作区 `note.md`（不是临时聊天里消失），并征求用户确认要改哪些。

### Step 4 — 改写 + Dry-run + 提交

每张 card 的改写流程：

1. 用 `mcp__PostgreSQL__query`（或 Metabase MCP `metabase_query`）跑新 SQL 验证无错 + 行数合理 + 关键 case 正确
2. 跑"前后对比"数值（例：原 "需采购 SPU" 215 → 新 179，少 36 个误报）让影响可量化
3. 通过 `PUT /api/card/:id` 提交，**必须同时保留 dataset_query/display/visualization_settings/parameters**，否则会丢可视化配置
4. 冒烟测：`POST /api/card/:id/query` 拿 row_count 和 error
5. 备份原 SQL 到会话级 `.context/sql_backup_<date>/`

详细脚本见 `references/sop.md` §提交模板。

### Step 5 — 多轮迭代（用户提反例必须重打开 review）

**当用户给出"反例"时**（如"这条数据怎么算 ✅，明明 amz 3k 件、网站 233 件、价格一样"），不要解释为什么之前判定对，**立即去数据库捞这条记录的完整字段**，包括：
- 原始价格/终价/各种 discount/subsidy/cutting
- 跨表关联（采购单 + 采购计划 + 阶梯配置）
- 同 SKC/同 SKU 的历史轨迹

很多时候反例会揭示**新的真相字段**（如 `original_price`、`purchase_mode`、`ladder_discount_detail`），需要回到 Step 2 重做语义验证。

### Step 6 — 美化（列数 ≥ 12 时启动，路由到 metabase-beautify skill）

**当需要美化时，调用 metabase-beautify skill 执行**。核心动作：列数压到 ≤ 11，不删原始数字列（设 `enabled: false`）。

常用配方：可售天数+状态色带、库存分布合并、行动建议合一、SPU 等级 emoji、行级背景染色、导出友好 table.columns 配置。

详细配方集见 metabase-beautify SKILL.md。

### Step 7 — 筛选项工程（用户说"加筛选/搜索/下拉"时触发，详见 filters-cookbook.md）

**触发条件**：
- 用户说"加筛选项 / 加下拉 / 加搜索 / 让运营能选 X"
- 用户说"切换店铺 / 切换市场 / 按 SPU 钻取"但当前看板没参数
- 用户说"question 直链不应用默认值"
- 用户说"我筛选了美国还看到加拿大的数据" — 通常是漏 wire 或 join 没带 marketplace

**三层架构**（任何一层缺失都失效）：
1. **单卡 SQL**：定义 template-tag（`[[ AND ... = {{tag}} ]]` + required + default）
2. **Dashboard 参数**：顶部 parameter + `values_source_type='card'` 配 lookup card
3. **桥接层**：每张 dashcard 的 `parameter_mappings` 路由顶部参数 → 卡内 template-tag

**关键决策**：
- 数量 ≤ 20 → **下拉**（`values_query_type='list'` + lookup card）
- 数量 > 100 → **输入时搜索**（`values_query_type='search'` + lookup card）
- 用户友好命名 → SQL 内部用 lookup 表把"美国"翻译回 `ATVPDKIKX0DER`
- 必填筛选 → `required: true` + `default`（否则 question 直链不应用 default）

**常见配方**（详见 `references/filters-cookbook.md`）：
- 中文名 → ID 翻译（lookup `code_library`）
- 多键 OR 解析（用户填任一筛选项都生效）
- 时间区间 + 粒度
- lookup card 模板（店铺/市场/parent_asin/cider_spu/skc/sku 等）
- 完整工作流脚本（一次性配齐 11 个筛选 × N 张卡）

**完成前 checklist**（见 filters-cookbook.md 末尾）。

### Step 8 — 沉淀（每轮必做）

**每完成一轮**都要追加到 `note.md`，结构：
- 日期+主题（如 `## 2026-05-23 1582 v3: 修计划下单量口径`）
- bug 名 + 数据证据 + 修复公式
- 关键数据库知识（如 "purchase_mode=1 表示阶梯/补贴模式，pure_flat 24.7%"）
- 新发现的字段语义陷阱 → 同步到 `references/known-pitfalls.md`

未来同类需求可直接 grep note.md 复用，避免重复踩坑。

---

## Anti-pattern（已踩坑，禁止）

- ❌ 看 SQL 字面意思就下结论 → 必须实测字段
- ❌ 用户说"再加一列"就直接加 → 先评估列数是否需要美化压缩
- ❌ 改完不冒烟测 → 必须 POST `/api/card/:id/query` 验证 status=completed
- ❌ PUT card 时只发 dataset_query → 会丢失 visualization_settings，必须 GET 后 merge
- ❌ 解释"为什么之前的判定是对的" → 用户提反例时必须无条件回到数据库验证
- ❌ 漏掉 description 更新 → 改完口径必须把"列含义说明"写进 card description，运营能 hover 看到
- ❌ 把 review 报告只写在聊天里 → 必须落地到 `note.md`

---

## 参考资料

- `references/sop.md` — 拉 SQL / PUT card / 冒烟测的完整命令模板
- `references/known-pitfalls.md` — 已踩过的字段语义陷阱（持续更新）
- `references/visualization-cookbook.md` — Metabase 可视化设置常用配方（条件格式/列宽/图表类型）
- `references/filters-cookbook.md` — **筛选项工程**（下拉/搜索/中文名翻译/dashboard wire-up + 检查清单）
- `metabase-beautify` skill — **表格美化**（独立 skill，列数压缩/emoji 状态/库存分布/导出友好）

---

## 元规则：本 skill 自身的进化

每次发现新的字段陷阱、新的 Metabase API 用法、新的"看 SQL 字面意思就下错结论"的反例，都要追加到 `references/known-pitfalls.md`，让下一次执行此 skill 的 Agent 不再踩同样的坑。
