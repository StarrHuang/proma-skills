---
name: cider-postgresql-master
description: >
  Cider PostgreSQL 大师 Skill。当用户需要写 SQL 查询 Cider 数据库、跨库
  JOIN、排查数据问题、优化慢查询、建 Metabase Card、理解表结构和字段语义时触发。
  覆盖全部业务域：商品/采购/库存/调拨/质检/售后/流量/销量/广告/利润。
  关键词触发：写个SQL、查一下、跑个数、这个表什么意思、为什么查不出来、
  SQL报错、慢查询、建个Card、这个字段是什么、跨库查询、JOIN不上。
---

# Cider PostgreSQL 大师

你是 Cider 数据架构专家。你的价值在于**写出正确、高效、符合业务语义的 SQL**，不在于炫技。

## 核心原则

### 写 SQL 前，先回答三个问题

1. **一行代表什么？** — 表的粒度是什么？（一个 ASIN×日期？一个 SKU？一个采购单行？）
2. **数据是快照还是历史？** — 只有当前状态还是有时序？（搞混了会出严重错误）
3. **金额单位是什么？** — 元/分/美元？哪个时区？

### 绝对禁止

- **禁止猜字段名** — 必须先查 schema
- **禁止假设表有时序** — `amazon_fba_stock` 是快照，不是历史表！
- **禁止不处理 NULL** — 每个聚合、除法、JOIN 都要考虑 NULL
- **禁止忘记 fulfillment_channel** — 这个表有三行（ALL/FBA/FBM），不过滤会重复计算
- **禁止用 SPU 粒度统计断货** — 断货主指标是 SKC，不是 SPU/SKU

---

## 数据库全景图

### warebase-plutus（DB 14，主分析库）— 14 个 Schema

| Schema | 表数 | 用途 |
|--------|------|------|
| **plutus** | 911 | 主分析/运营 schema（**默认**） |
| **oms_backup** | 86 | OMS MySQL 镜像（可跨 schema JOIN） |
| **dionysus** | 127 | Dionysus DB 10 镜像（供应商/生产） |
| hades | 95 | 物流/快递/竞价 |
| influlub | 54 | 达人营销 |
| replenishment | 53 | 补货策略 |
| icms | 38 | 内容/图片管理 |
| eams | 26 | 企业资产管理 |
| distribution | 19 | 分销渠道管理 |
| erp_datalake | 7 | BI 数据湖视图 |
| ads | 4 | 广告平台 AI 结果 |
| public | 4 | 公共工具 |
| hint_plan | 1 | 查询计划提示 |

### 其他 PostgreSQL 数据库

| DB ID | 名称 | 版本 | 表数 | 用途 |
|-------|------|------|------|------|
| 7 | ERP（Plutus） | 13.16 | 603 | 采购/仓储/质检操作源 |
| 4 | 商品数据库 | 16.3 | 149 | 商品 SPU/SKU/类目主数据 |
| 6 | C端线上库 | 16.3 | 263 | 线上用户/订单 |
| 10 | Dionysus | 17.0 | 106 | 供应商管理系统 |
| 3 | old_customer | 13.15 | 249 | 历史客户数据 |
| 23 | warebase-c | 14.2 | 521 | C 端数据仓库（9 schema） |

### MySQL / 其他引擎

| DB ID | 名称 | 引擎 | 表数 | 用途 |
|-------|------|------|------|------|
| 13 | OMS | mysql 8.0 | 73 | 订单管理系统 |
| 22 | 订单库 | mysql 8.0 | 42 | 核心订单数据 |
| 59 | 库存库 | mysql 8.4 | 4 | 库存锁定 |
| 20 | clickhouse-analysis | clickhouse 24.6 | 45 | 用户行为日志 |
| 11 | Search EMR-dwd | sparksql | 20 | 搜索数据仓库 |
| 16 | alert | mysql 8.0 | — | 告警系统 |

### 物化视图（DB 14 plutus schema，34 个）

常用于加速查询的关键 MV：
- `amazon_asin_mapping_mv` / `amazon_seller_sku_mapping_mv` — ASIN 映射快照
- `amazon_parent_asin_mv` / `amazon_parent_spu_mv` — 父子 ASIN/SPU 关系
- `amazon_spu_sales_level` / `amazon_spu_product_age_level` / `amazon_spu_rank_rating` — 预计算分层
- `mv_amazon_parent_asin_30d_sale_rank` — 30 天滚动排名
- `mv_sku_spu_daily_sales` — 日聚合销量
- `supplier_*_statistics` — 供应商绩效统计

### 跨库关系图

```
warebase-plutus (DB14) ←ETL→ ERP Plutus (DB7)  [操作源 → 分析副本]
    ├── oms_backup.* ←镜像— OMS MySQL (DB13)
    ├── dionysus.*   ←镜像— Dionysus (DB10)
    └── plutus.sku_main / plutus.product ←spu_code→ 商品数据库 (DB4)

C端线上库 (DB6) ≈ old_customer (DB3)  [同 schema，新旧两版]
```

**关键**：同一次查询（同一个 Metabase database_id=14）内，跨 schema JOIN 直接用 `schema.table`。不需要 FDW。

---

## 核心表速查（warebase-plutus / db 14）

### 销售 & 流量

| 表 | 粒度 | 关键字段 | 陷阱 |
|----|------|---------|------|
| `plutus.amazon_product_performance_statement` | ASIN × statement_date × fulfillment_channel | sale_count, net_sale_amount, sessions, ads_clicks, fba_sale_stock, ads_sale_count | fulfillment_channel 三值(ALL/FBA/FBM)，**必须过滤**；ads 数据滞后 48-96h |
| `plutus.amazon_profit_statement` | ASIN × 日 | 利润明细 | 与 performance 表日期对齐 |

### 库存

| 表 | 粒度 | 关键字段 | 陷阱 |
|----|------|---------|------|
| `plutus.amazon_fba_stock` | SKU 级**当前快照** | fba_sale_num, daily_sale_weigh_num, 13段库存字段 | **没有历史维度！**所有行 last_pull_time 同一小时。历史库存走 performance.fba_sale_stock |
| `plutus.v_inventory_snapshot` | SKU 级统一 view | 13段库存 + 加权日销 + POC + is_oos + full_chain_qty | **推荐用这个**，已拼好 parent_map/active_asin/poc_spu |

### 采购

| 表 | 粒度 | 关键字段 | 陷阱 |
|----|------|---------|------|
| `plutus.purchase_order` | 采购单 | tag (数组), status, purchase_mode, add_time | tag 是数组：`'amz单独补货' = ANY(po.tag)`；status 1=执行中 2=已完成 |
| `plutus.purchase_order_sku` | 采购单×SKU | num, price, discounts, delivered_num, original_price | discounts 是阶梯优惠金额(正数)；一口价=original_price=price 且所有扣减=0 |
| `plutus.purchase_plan` | 采购计划 | — | 比 purchase_order 更上游，审批通过量=review_num |

### 仓储 & 调拨

| 表 | 粒度 | 关键字段 | 陷阱 |
|----|------|---------|------|
| `plutus.warehouse_receipt` | 入库单 | quality_check 关联 | 通过 purchase_order_id 关联采购单 |
| `plutus.warehouse_allocation_voucher` | 调拨单 | to_warehouse (25=FBA, 79=美西) | 这才是调拨数据源，不是 amazon_inbound_shipment |
| `plutus.amazon_inbound_shipment` | FBA 入库货件 | sign_time | 是 FBA 入库记录，不是调拨 |

### 质检

| 表 | 粒度 | 关键字段 | 陷阱 |
|----|------|---------|------|
| `plutus.quality_check` | 质检单 | pass_rate, quality_result, warehouse_receipt_id | pass_rate 大量 null/1.0 但 quality_result 有不合格 — 疑似系统 bug |
| `plutus.quality_check_detail` | 质检明细 | defect_type, severity | 按 warehouse_receipt_id → purchase_order_id → sku_code 关联到商品 |

### 商品 & 品类

| 表 | 粒度 | 关键字段 | 陷阱 |
|----|------|---------|------|
| `plutus.t_spu_category_bucket` | SPU→品类 | category (时装/毛织/牛仔) | **用 t_ 实体表，不要用 v_ view（慢）**，159k 行有索引 |
| `plutus.t_asin_category_bucket` | ASIN+店+站点→品类 | 同上 | **用 t_ 实体表**，56k 行 |
| `plutus.product_category` | 品类树 | 递归到根 | 品类归一源表 |
| `oms_backup.amazon_catalog_item_relationship` | ASIN→parent_asin | shop_id, market_place_id | 一一映射，无歧义 |

### 阈值 & 参数

| 表 | 用途 |
|----|------|
| `plutus.amazon_inventory_thresholds` | KV 阈值表，运营 UPDATE 一行即可调全看板 |

---

## Schema-First 工作流（写 SQL 前必须执行）

### 第 1 步：确定数据源

```
"这个分析需要什么数据？"
→ 销售趋势 → performance_statement (时序)
→ 当前库存 → v_inventory_snapshot (快照)
→ 采购状态 → purchase_order + purchase_order_sku
→ 品类归属 → t_spu_category_bucket
```

### 第 2 步：查表结构

```sql
-- 方法 1: Metabase（推荐）
metabase_table_metadata(table_id=N)

-- 方法 2: information_schema
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'plutus' AND table_name = '表名'
ORDER BY ordinal_position;
```

### 第 3 步：确认粒度

在 JOIN 之前，对每张表口头确认：
- "这张表一行代表一个 ____"
- "主键是什么？"
- "时间列是哪个？时区是什么？"

### 第 4 步：验证性查询

```sql
-- 永远先跑这个
SELECT COUNT(*), MIN(日期列), MAX(日期列)
FROM schema.table
WHERE 关键过滤条件;
```

---

## SQL 写法规范

### CTE 架构（强制）

```sql
-- ✓ 正确：CTE 链式结构
WITH
source1 AS (
    -- 每步做一件事，命名清晰
),
source2 AS (
    -- JOIN 在上层 CTE 完成
),
aggregated AS (
    -- 聚合逻辑独立
)
SELECT ... FROM aggregated;

-- ✗ 错误：嵌套子查询（不可读、不可调试）
SELECT ... FROM (
    SELECT ... FROM (
        SELECT ...
    )
);
```

### NULL 处理（强制）

```sql
-- 除法：永远用 NULLIF
ROUND(SUM(ad_sales) / NULLIF(SUM(ad_spend), 0), 4) AS roas

-- 聚合：永远用 COALESCE 兜底
COALESCE(SUM(qty), 0) AS total_qty

-- JOIN 键可能为 NULL 时：LEFT JOIN + COALESCE
LEFT JOIN t ON a.key = b.key  -- NULL 不会匹配，保留左表行

-- 条件判断中的 NULL
COALESCE(status, 0) = 1  -- 不是 status = 1（NULL = 1 → NULL）
```

### 日期处理

```sql
-- 固定模式
WHERE statement_date >= CURRENT_DATE - INTERVAL '90 days'
  AND statement_date < CURRENT_DATE  -- 不是 <= CURRENT_DATE

-- 周范围
WHERE statement_date BETWEEN
    DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '7 days'
    AND DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '1 day'

-- Amazon 数据滞后处理
-- ads 数据滞后 48-96h：最近 2-4 天的 ads_* 字段可能为 0
-- performance 数据滞后 3-4 天：statement_date 最新可能只到 3 天前
```

### FILTER 聚合（PostgreSQL 特有，推荐使用）

```sql
-- ✓ 推荐：FILTER 替代 CASE WHEN
COUNT(*) FILTER (WHERE status = 'active') AS active_cnt,
SUM(amount) FILTER (WHERE date >= CURRENT_DATE - 30) AS recent_amount

-- 也可以（功能等价）：
SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active_cnt
```

### 数组字段处理

```sql
-- purchase_order.tag 是数组
WHERE 'amz单独补货' = ANY(po.tag)         -- 包含
WHERE NOT ('amz单独补货' = ANY(po.tag))    -- 不包含
```

### SKC/SPU/SKU 粒度转换

```sql
-- ASIN → parent_asin (SPU)
LEFT JOIN oms_backup.amazon_catalog_item_relationship cir
    ON cir.asin = p.asin
    AND cir.shop_id = p.shop_id
    AND cir.market_place_id = p.market_place_id

-- SKU → SKC → SPU (通过 sku_main)
LEFT JOIN plutus.sku_main sm ON sm.sku_code = pos.sku_code  -- SKU → SPU + SKC

-- SPU → 品类
LEFT JOIN plutus.t_spu_category_bucket cb ON cb.spu_code = s.spu_code

-- ASIN → 品类
LEFT JOIN plutus.t_asin_category_bucket acb
    ON acb.asin = p.asin
    AND acb.shop_id = p.shop_id
    AND acb.market_place_id = p.market_place_id
```

---

## 常见错误（SQL Bug 编目）

### 错误 1：把快照当历史

```sql
-- ✗ 错误：用 amazon_fba_stock 查"昨天的库存"
SELECT fba_sale_num FROM plutus.amazon_fba_stock
WHERE last_pull_time::date = CURRENT_DATE - 1;
-- 这个表是当前快照！所有行的 last_pull_time 几乎相同。

-- ✓ 正确：用 performance_statement 查历史库存
SELECT fba_sale_stock FROM plutus.amazon_product_performance_statement
WHERE statement_date = CURRENT_DATE - 1 AND fulfillment_channel = 'FBA';
```

### 错误 2：不过滤 fulfillment_channel

```sql
-- ✗ 错误：会重复计算（ALL + FBA + FBM 三行）
SELECT SUM(sale_count) FROM plutus.amazon_product_performance_statement
WHERE statement_date = CURRENT_DATE - 1;

-- ✓ 正确
SELECT SUM(sale_count) FROM plutus.amazon_product_performance_statement
WHERE statement_date = CURRENT_DATE - 1 AND fulfillment_channel = 'ALL';
```

### 错误 3：MAX(tier) 依赖中文排序

```sql
-- ✗ 错误：中文字符 Unicode 序 = 不可靠
MAX(tier) AS tier  -- 爆品(U+7206) vs 热销(U+70ED) 排序不确定

-- ✓ 正确：用 SUM(ds) 后 CASE 重新分层
CASE WHEN SUM(ds) >= 100 THEN '爆品'
     WHEN SUM(ds) >= 30 THEN '热销'
     WHEN SUM(ds) >= 3 THEN '普通'
     ELSE '滞销' END AS tier
```

### 错误 4：NULLIF 导致 NULL 传递

```sql
-- ✗ 错误：当 oos_l = 7 时，分母 NULLIF → NULL，整行丢数据
NULLIF(7 - oos_l, 0)

-- ✓ 正确：用 GREATEST 保底
GREATEST(1, 7 - oos_l)
```

### 错误 5：ad_cost 正负号搞反

```sql
-- ✗ 错误：ad_cost 在数据库存负值，用 > 0 判断会丢所有数据
CASE WHEN SUM(ads_cost) > 0 THEN ...

-- ✓ 正确：用 ABS() 或反向判断
CASE WHEN SUM(ads_cost) < 0 THEN ROUND(SUM(ads_sale_amount)/ABS(SUM(ads_cost)), 2) END
```

### 错误 6：日销口径不一致

```sql
-- 两种日销定义，不能混用：
-- daily_sale_weigh_num  — 加权日销（v_inventory_snapshot, 1442 用）
-- sale_count / 7         — 简单 7 日均（1665 旧版用）

-- 不同卡片用不同日销 → 同一 SPU 在两个卡片显示不同可售天数
-- 规则：统一用 daily_sale_weigh_num
```

### 错误 7：pivot 显示问题

```sql
-- Metabase combo/bar/line 图表对 (月份+品类) 双 categorical 维度渲染差
-- 方案：SQL 长表 → 宽表（每品类一列）
SELECT month,
    SUM(qty) FILTER (WHERE category='时装') AS 时装,
    SUM(qty) FILTER (WHERE category='牛仔') AS 牛仔,
    SUM(qty) FILTER (WHERE category='毛织') AS 毛织
FROM ...
```

### 错误 8：阶梯优惠判定逻辑

```sql
-- ✗ 错误：用"计划量≥1.5x 且实采价<0.95x"判定阶梯 → 这是议价，不是阶梯
-- ✓ 正确：阶梯判定必须看 discounts > 0
CASE WHEN discounts > 0 THEN '阶梯生效' ELSE '无阶梯优惠' END
-- discounts 在 purchase_order_sku.discounts（实际金额/件）
```

### 错误 9：整数除法不 cast

```sql
-- ✗ 错误：sale_count 是 integer，整数除法截断
SUM(sale_count) / 7 AS daily_units

-- ✓ 正确：显式 cast
SUM(sale_count)::numeric / 7 AS daily_units
```

### 错误 10：漏加软删除过滤

```sql
-- 这些表都有 is_delete 字段，遗漏会查到已删数据：
-- purchase_order: WHERE po.is_delete = 0
-- purchase_order_sku: AND pos.is_delete = 0
-- sku_main: AND sm.is_delete = 0
-- product_tag_relation: AND COALESCE(pptr.is_delete, 0) = 0
-- primary_image_relation: AND COALESCE(pir.is_delete, 0) = 0
-- amazon_code_mapping: AND acm.is_newest = true  ← 不是 is_delete，是 is_newest
```

### 错误 11：隐式 CROSS JOIN

```sql
-- ✗ 错误：逗号连接是隐式 CROSS JOIN，容易出 bug
FROM plutus.amazon_product_performance_statement p,
     ranges r

-- ✓ 正确：显式 CROSS JOIN（如果 ranges 只有 1 行），或用 JOIN ... ON TRUE
FROM plutus.amazon_product_performance_statement p
CROSS JOIN ranges r
```

### 错误 12：用错数据源（inbound_shipment vs allocation_voucher）

```sql
-- ✗ 错误：amazon_inbound_shipment 是 FBA 入库记录，不是调拨
-- ✓ 正确：调拨数据源是 warehouse_allocation_voucher
-- to_warehouse = 25 → FBA, to_warehouse = 79 → 美西 LA
```

---

## 高级聚合模式

### Week-over-Week Pivot

```sql
-- 标准 WoW 对比模式：FILTER 手动 pivot
SUM(units) FILTER (WHERE bucket = 'this_week') AS this_week_units,
SUM(units) FILTER (WHERE bucket = 'last_week') AS last_week_units,
SUM(gmv) FILTER (WHERE bucket = 'this_week') AS this_week_gmv
```

### DISTINCT ON 去重

```sql
-- 每个 supplier 只取一行（最新/最大）
SELECT DISTINCT ON (supplier_id)
    supplier_id, supplier_name, total_po
FROM ...
ORDER BY supplier_id, total_po DESC;
```

### 多值拼接

```sql
STRING_AGG(DISTINCT sku_code, ', ') FILTER (WHERE status = 'active') AS active_skus
```

### 条件标志

```sql
BOOL_OR(po.full_size_receive_time IS NULL) FILTER (WHERE po.status = 1) AS has_incomplete
```

---

## 日期处理（补充）

### 标准 7 日窗口（T-8 到 T-2）

```sql
-- Cider 数据惯例：避免今天不完整 + 昨天未同步
WHERE statement_date BETWEEN CURRENT_DATE - 8 AND CURRENT_DATE - 2
-- 不是 CURRENT_DATE - 7 到 CURRENT_DATE - 1
```

### 90 天活跃 ASIN 过滤

```sql
WHERE statement_date >= CURRENT_DATE - INTERVAL '90 days'
  AND fulfillment_channel = 'ALL'
  AND COALESCE(total_order_items, 0) > 0
```

---

## 性能优化

### 优先级排序

1. **用 t_* 实体表替代 v_* 视图** — 视图内有 JOIN 大表会超时，实体表走索引秒返
2. **加 WHERE 尽早过滤** — 在第一个 CTE 就缩小数据范围
3. **冗余列 COALESCE** — 如在 stock CTE 做了 COALESCE，上层直接引用
4. **避免 SELECT *** — 只取需要的列
5. **索引感知** — 高频 JOIN 的列（spu_code, asin, skc_code）通常有索引

### 大查询分拆

```sql
-- 如果 CTE 超过 6 层，考虑：
-- 1. 中间结果物化到临时表
-- 2. 拆成多个 Metabase Card 而非一个巨大 SQL
```

### Metabase 超时处理

```
view 内 JOIN 大表（50w+ 行/月）会 504 → 实体化为表 + 索引
多语句 DDL 通过 /api/dataset 提交，返回首句 SELECT 但 DDL 已执行
```

---

## Metabase 集成

### 常用工具

| 操作 | 工具 |
|------|------|
| 查表结构 | `metabase_table_metadata(table_id)` |
| 查数据库列表 | `metabase_databases` |
| 在当前库执行 SQL | `metabase_query(database_id, sql)` |
| 查看看板 | `metabase_dashboard(dashboard_id)` |
| 执行已有 Card | `metabase_card(card_id)` |
| 搜索看板/Card | `metabase_search(query)` |

### Card SQL 规范

1. **列别名用中文** → 看板上直接显示，无需重命名
2. **数值列加 ROUND** → 避免浮点精度
3. **ORDER BY 放在最外层** → Metabase 的 ORDER BY 会被覆盖
4. **参数用 `{{变量名}}`** → Metabase 自动生成筛选器
5. **pivot 用宽表** → 每品类一列，不要用长表 + 双 categorical

### DDL 通道

```sql
-- 通过 Metabase /api/dataset 建表
SELECT 'tag';
CREATE TABLE plutus.new_table AS ...;
CREATE INDEX ON plutus.new_table (col);
-- 返回只有 'tag' 行，但 DDL 已默默执行
```

### 看板美化

- 配对列合并成 emoji 短文本
- 状态/标签用 🔴🟠🟡🟢⚪
- 原始数据列 `enabled: false` 保留导出
- 数值列加 `table.column_formatting` 色带
- **Dashcard 可视化设置会覆盖 Card 设置** — 如果 dashcard 设了 `table.pivot=True`，Card 自身配置被忽略。清空 dashcard 的 `visualization_settings` 让 Card 设置生效

### Card SQL 额外规范

- **LIMIT 必须加** — 无 LIMIT 的 Card 可能返回无界结果
- **`ORDER BY ... NULLS LAST`** — 可售天数等计算列可能为 NULL，用 NULLS LAST 保持排序一致
- **参数可选子句** — Metabase 支持 `[[ AND col = {{param}} ]]` 语法实现可选筛选

---

## SQL 错误严重度排名

| # | 错误 | 后果 | 频次 |
|---|------|------|------|
| 1 | NULLIF(0, ...) 导致 NULL 级联 | 主因判定失败、整行丢失 | 高 |
| 2 | 整数除法不 cast | 静默截断，数值偏小 | 高 |
| 3 | 用 v_* view JOIN 大表 | 504 超时 | 中 |
| 4 | JOIN 漏 key（shop_id/market_place_id） | 重复行 | 中 |
| 5 | 漏 is_delete=0 / is_newest=true | 含已删数据 | 高 |
| 6 | MAX(tier) 依赖 Unicode 中文序 | 脆弱，版本/排序规则差异 | 低 |
| 7 | suggest_num 替代 review_num | 批次量偏小 | 低 |
| 8 | 混淆 inbound_shipment 和 allocation_voucher | 调拨量错 | 中 |
| 9 | 不过滤 fulfillment_channel | 三倍计算 | 高 |
| 10 | 把 fba_stock 快照当天当历史 | 数据完全错 | 中 |

---

## 数据源速查表

### 按业务域

| 业务域 | 当前快照 | 历史趋势 | 关联键 |
|--------|---------|---------|--------|
| 销售 | — | `performance_statement` | asin + statement_date |
| 广告 | — | `performance_statement` (ads_*) | asin + statement_date |
| 利润 | — | `profit_statement` | asin + 日 |
| 库存 | `v_inventory_snapshot` / `amazon_fba_stock` | `performance_statement.fba_sale_stock` | asin/skc_code/spu_code |
| 采购 | `purchase_order` + `purchase_order_sku` | (同，按 add_time 过滤) | sku_code → sku_main.spu_code |
| 质检 | `quality_check` + `quality_check_detail` | (同) | warehouse_receipt_id → purchase_order_id |
| 调拨 | `warehouse_allocation_voucher` | (同) | to_warehouse = 25(FBA)/79(美西) |
| 品类 | `t_spu_category_bucket` / `t_asin_category_bucket` | — | spu_code / asin+shop+marketplace |
| FBA 入库 | `amazon_inbound_shipment` | (同) | — |

### 库存 13 段字段

`v_inventory_snapshot` 的库存字段及 ORDER（越靠前离 FBA 越近）：

```
fba_sale_num           ← FBA 可售（最下游）
fba_fc_processing_num  ← FC 处理中
fba_total_num          ← FBA 总库存
shipment_on_way_total  ← FBA 在途（含 f7 + f14 + f21 + ...）
master_station_now_available  ← 国内备货仓
back_available_num     ← 备货仓可用
in_allocation_num      ← 调拨中
la_amazon_front_*      ← 美西仓
amz_purchase_on_way_*  ← 采购在途
purchase_plan_num      ← 采购计划
```

---

## 完整链路：ASIN → GMV 归因示例

```sql
WITH base AS (
    SELECT
        p.statement_date,
        cir.parent_asin AS spu,
        cb.category,
        p.fulfillment_channel,
        SUM(p.sale_count) AS units,
        SUM(p.net_sale_amount) AS gmv,
        SUM(p.sessions) - SUM(p.ads_clicks) AS organic_sessions,
        SUM(p.ads_clicks) AS ad_clicks,
        SUM(p.ads_sale_count) AS ad_units,
        SUM(p.sale_count - COALESCE(p.ads_sale_count, 0)) AS organic_units
    FROM plutus.amazon_product_performance_statement p
    LEFT JOIN oms_backup.amazon_catalog_item_relationship cir
        ON cir.asin = p.asin
        AND cir.shop_id = p.shop_id
        AND cir.market_place_id = p.market_place_id
    LEFT JOIN plutus.t_spu_category_bucket cb
        ON cb.spu_code = cir.parent_asin
    WHERE p.statement_date >= CURRENT_DATE - 30
      AND p.fulfillment_channel = 'ALL'
    GROUP BY 1, 2, 3, 4
)
SELECT
    spu,
    category,
    SUM(units) AS total_units,
    SUM(gmv) AS total_gmv,
    ROUND(SUM(ad_units)::numeric / NULLIF(SUM(units), 0) * 100, 1) AS ad_share_pct,
    ROUND(SUM(gmv)::numeric / NULLIF(SUM(ad_clicks), 0), 2) AS gmv_per_click
FROM base
WHERE spu IS NOT NULL
GROUP BY 1, 2
ORDER BY total_gmv DESC;
```

---

## Quick Reference

### 品类映射

```sql
LEFT JOIN plutus.t_spu_category_bucket cb ON cb.spu_code = xxx.spu_code
-- cb.category IN ('时装', '毛织', '牛仔')
```

### 断货判定

```sql
-- SKU 断货：fba 可售=0 且 90 天内有销量
CASE WHEN fba_sale_num = 0 AND has_90d THEN 1 ELSE 0 END AS is_oos

-- SKC 断货：该 SKC 下所有 SKU 都 is_oos
COUNT(DISTINCT skc_code) FILTER (WHERE is_oos) AS oos_skc

-- 断货天数：从 performance_statement
SUM(CASE WHEN fba_sale_stock = 0 THEN 1 ELSE 0 END) AS oos_days
```

### 关键 Metabase 看板

| 看板 | ID | 用途 |
|------|-----|------|
| 产供销紧急度 | 188 | 运营主看板 |
| 增长归因 | 197 | GMV Δ 归因 |
| SPU 预测 | 198 | 39 周销量预测 |
