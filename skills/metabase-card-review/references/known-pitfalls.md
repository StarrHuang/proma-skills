# 已踩过的字段语义陷阱

> 每次发现新陷阱要追加到这里。格式：表名+字段 → 现象 → 正解。

## 亚马逊数据（plutus schema）

### `amazon_product_performance_statement.fulfillment_channel`
- 取值 `'ALL' / 'FBA' / 'FBM'`，**ALL 行是预聚合 = FBA + FBM**
- `fba_sale_stock` 在 ALL/FBA 行同值，FBM 行=0
- **陷阱**：同时 JOIN ALL+FBA 会 ×3 重复；想要单一总量取 'ALL' 即可

### `amazon_fba_stock.daily_sale_weigh_num` vs `amazon_product_performance_statement.sale_count/7`
- daily_sale_weigh_num = 加权日销（含衰减/补偿），是字段层面的"成品日销"
- sale_count/7 = 算术平均，更适合趋势趋势查询
- **不要混用做分母**，否则跨卡口径分裂

### `amazon_fba_stock` 是当前快照
- 所有行 `last_pull_time` 集中在同一小时，**没有历史**
- 趋势分析必须走 `amazon_product_performance_statement.fba_sale_stock`

### `shipment_on_way_total_num` ≠ f7+f14+f21
- total 包含**全时效**（7/14/21/更长），实测 total=162k 而 7+14+21=39k
- **陷阱**：并列展示 total/7d/21d 会被误解为加总
- 正解：只展示 total，或拆成互斥三桶 `[7天内 / 8-21天 / 22天+]`

### `oms_backup.amazon_catalog_item_relationship`
- (shop_id, marketplace_id, asin) → parent_asin 一对一映射，无歧义
- 一个 parent_asin 可下挂多个 child_asin（avg 6, max 144）

### `master_station_now_available_num` vs `back_available_num`
- 两个不同仓：备货仓（肇庆）vs 主站现货仓
- 可以相加，量级各有 25 万件

### `amazon_fba_stock.fba_total_num` vs `fba_sale_num + fba_reserved_num`
- `fba_total = sale + reserved`，**不含** `fba_fc_processing_num`
- 想算"FBA 已锁定库存"应 = total + fc_processing

## 采购数据

### `purchase_order_sku.suggest_num` vs `purchase_plan_sku.review_num`
- `purchase_order_sku.suggest_num` 是采购单的"建议数"，**已被跟单分拆**
- 原始批量在 `purchase_plan_sku.review_num`（审批通过数量）
- 看"单次计划下单量"必须用 plan_sku 不是 order_sku

### `purchase_order_sku.price` vs `original_price`
- 注释：`price = original - 阶梯优惠 - 散剪费`
- 还有 3 类补贴：`profit_subsidy / small_order_loss_subsidy / satin_fabric_subsidy`
- 一口价判定：`original_price = price AND discounts=0 AND 3 类补贴都=0`

### `purchase_order.purchase_mode`
- 1 = 阶梯/补贴模式（pure_flat 仅 24.7%）
- 2 = 一口价主流（pure_flat 77.7%）
- 3 = 期价/合作模式（55.6%）
- 5 = 纯一口价（100% pure_flat）
- 全店 78% SKC 是一口价为主——解释为何 amz 阶梯命中率只 4.8%

### `purchase_order_sku.ladder_discount_detail` (jsonb)
- 字段名注释"阶梯优惠明细"
- 实际 JSON 结构: `{woolenLadderDiscountsDetail, cuttingLadderDiscountsDetail, fabricWastageDiscountsDetail, managementFeeDiscountsDetail}`
- `.logs[]` 含字符串 `"命中XX阶梯, config purchaseNumMin N, config purchaseNumMax M, purchaseNum X, discountRate R, discount D"`
- 反推阶梯档位用 regex_match 字符串
- **`discounts` 字段** 才是真正拿到的阶梯优惠金额/件（数值），用它判定是否生效，不要看 logs 文本

### 阶梯价配置表不在数据库
- 只能从 `ladder_discount_detail.logs` 反推**已命中过的**档位
- 完整阶梯配置在核价微服务后端，DB 查不到

## SQL 写法陷阱

### `MAX(text_column)` 按 Unicode 排
- `MAX('爆品','热销','普通','滞销')` = '爆品' 是**巧合**（Unicode 序），加个 '神级' 就崩
- 正解：先 SUM 数值后 CASE 重新分层

### `NULLIF(x, 0)` 在边界返回 NULL
- 当除数可能为 0 时 NULLIF 是对的；但 NULL 会污染下游 ABS/GREATEST 比较
- 临界情况用 `GREATEST(1, x)` 退化为有效值更安全

### ORDER BY 别名（PostgreSQL）
- PG 不支持 `ORDER BY "中文别名"` 引用 SELECT alias 时的列
- 正解：在子查询里把 ORDER 列也 SELECT 出来，外层 ORDER BY 那个列

### `string_agg(DISTINCT ... ORDER BY ...)` 限制
- DISTINCT 和 ORDER BY 不能同时出现在 string_agg 里（PG < 16）
- 拆成两个 CTE：先 DISTINCT 子查询，再外层 string_agg 不带 DISTINCT

## Metabase 特定

### PUT /api/dashboard/:id 必须带 tab 信息
- v50+ dashboard 有 tabs 后，dashcard 必须带 `dashboard_tab_id`
- 漏掉报错：`Referential integrity constraint violation: FK_DASHBOARDCARD_TAB_ID`

### PUT /api/card/:id 必须携带 visualization_settings
- 只发 dataset_query 会清空可视化配置（列宽、条件格式、列设置）
- 正解：先 GET 完整 payload，merge 新字段，再 PUT

### Metabase /api/dataset 支持多语句 DDL
- 默默执行，仅返回首条 SELECT 的数据
- 前提：库账号有 CREATE 权限

### Metabase pivot 表的 column_split 字段格式
- 用 `[['field-literal', '<列名>', 'type/Text']]` 格式（看似 MBQL 但是 pivot 专用）
- values 用 `[['aggregation', 0]]` 指向第 0 个聚合
- 类型必须显式给（`type/Text` / `type/Integer` 等），漏写 pivot 不生效

### highlight_row 不适合大表
- `highlight_row: True` 整行染色仅适合 < 20 行的"汇总"型卡
- 在 100+ 行的列表卡用会让所有行都染色，等于没染

### MM-DD 跨年问题
- 用 TO_CHAR(time, 'MM-DD') 时间链节点，看起来短但跨年 12-31 → 01-02 视觉割裂
- 跨年场景用 `MM/DD/YY` 或在末尾加 'd' 表示天数

### Metabase question 直链不应用 required=false 的 default
- template-tag 设了 `default` 但没设 `required: true` 时, `/question/<id>` 直链访问且 URL 没传该参数 → `[[ AND ... ]]` 整段被跳过 → 默认值不生效
- Dashboard 内访问会应用 default, 但 question 详情链接不会
- **解法**: 所有"必填的"筛选项设 `required: true` + `default`

### amazon_catalog_item_relationship 必须三键 JOIN
- (asin, shop_id) 不够, 必须加上 marketplace_id
- 同一 child asin 在 US/CA/MX 会挂不同 parent_asin
  - 美国: B0CWK4PQJN → parent B0CWK2YJTR
  - 加拿大: B0CWK4PQJN → parent B0CY9GFG4R
- 漏掉 marketplace_id 会把美国销量错算到加拿大 parent_asin 上, parent_asin 维度数据全部污染
