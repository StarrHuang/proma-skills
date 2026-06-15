---
name: amazon-quality-investigation
description: Amazon SPU 大货质量深度调查。当用户提到某个 SPU 编码 + 质量问题/评分下滑/销售异常/调样确认/差评/退货率异常/做工问题/质检/供应商问题 等关键词时触发。系统化拉取 ERP 质检、销量、评分、退货、利润、库存、采购、FBA发货、调拨数据，生成飞书文档分析报告。
---

# Amazon SPU 大货质量深度调查

## 前置要求

MCP：`PostgreSQL` (plutus)、`metabase`、飞书 `lark-doc`。执行前读取 `skills/lark-doc/references/lark-doc-xml.md`、`skills/lark-doc/references/style/lark-doc-style.md`、`skills/lark-shared/SKILL.md`。

---

## 工作流

```
SPU输入 → 基础信息+开发员+跟单 → 质检通过率 → QC详情+缺陷 → 
采购+PO级QC+调拨+FBA → 销量+评分+退货+利润+库存 → 
ERP盲区 → 运营确认 → 旧版检查 → 深层挖掘 → 飞书报告
```

---

## 第一步：基础信息

### 1.1 产品与供应商
```sql
SELECT p.id, p.spu_code, p.supplier_id, s.supplier_name,
       p.develop_id, p.first_shelves_time, p.is_alive, p.status
FROM plutus.product p LEFT JOIN plutus.supplier1 s ON p.supplier_id=s.id
WHERE p.spu_code='<SPU>'
```

### 1.2 开发员（设计师）+ 跟单（采购负责人）
```sql
-- 开发员
SELECT id, name, email FROM plutus."user" WHERE id='<DEVELOP_ID>'
-- 跟单（purchase_order.purchase_uid，对供应商选择负责）
SELECT DISTINCT po.purchase_uid, u.name, u.email
FROM plutus.purchase_order po
JOIN plutus.purchase_order_sku pos ON pos.purchase_order_id=po.id
LEFT JOIN plutus."user" u ON po.purchase_uid=u.id
WHERE pos.sku_code LIKE '<SPU_PREFIX>%' AND po.purchase_uid IS NOT NULL
```
**⚠️ 跟单 (purchase_uid) 才是供应商选择和采购决策的责任人。开发员是设计师，不直接对供应商选择负责。报告中的责任人分析应聚焦跟单。**

### 1.3 SKU + ASIN
```sql
SELECT sm.sku_code, sm.sale_price, sm.cost_price, sm.skc_code,
       acr.asin, acr.parent_asin, acr.add_time
FROM plutus.sku_main sm
LEFT JOIN plutus.amazon_catalog_item_relationship acr ON sm.sku_code=acr.seller_sku
WHERE sm.spu_code='<SPU>' ORDER BY sm.sku_code, acr.add_time
```

### 1.4 同父 ASIN 下其他 SPU
```sql
SELECT DISTINCT sm.spu_code FROM plutus.sku_main sm
JOIN plutus.amazon_catalog_item_relationship acr ON sm.sku_code=acr.seller_sku
WHERE acr.parent_asin='<PARENT_ASIN>'
```

---

## 第二步：质检通过率

**⚠️ 正确公式：for_sale_num / receive_num（非 quality_check.pass_rate）**

```sql
SELECT sku.spu_code, wr.supplier_id, s.supplier_name,
       COUNT(*) as receipts, SUM(wrs.receive_num) as recv,
       SUM(wrs.for_sale_num) as sale,
       ROUND(SUM(wrs.for_sale_num)::numeric/NULLIF(SUM(wrs.receive_num),0)*100,2) as pass_rate,
       SUM(wrs.no_pass_num) as no_pass, SUM(wrs.refine_num) as to_refine
FROM plutus.warehouse_receipt wr
JOIN plutus.warehouse_receipt_sku wrs ON wrs.warehouse_receipt_id=wr.id
JOIN plutus.sku_main sku ON wrs.sku_id=sku.id
LEFT JOIN plutus.supplier1 s ON wr.supplier_id=s.id
WHERE wr.received_time IS NOT NULL AND sku.spu_code='<SPU>'
GROUP BY sku.spu_code, wr.supplier_id, s.supplier_name
```

---

## 第三步：QC 详情 + 缺陷

### 3.1 QC 方式
- `check_type=1` = **全检：100% 逐件检查，该批次全部货品都经过检验**
- `check_type=0` = **抽检：按 AQL 标准抽检部分货品**
- `actual_check_total` = 该批次实际检验总件数（全检时 = 批次总量）

### 3.2 缺陷明细
```sql
SELECT qcfd.flaw_name_level1, qcfd.flaw_name_level2,
       COUNT(*) as cnt, SUM(qcfd.flaw_num) as pcs
FROM plutus.quality_check_flaw_detail qcfd WHERE qcfd.spu_id=<PRODUCT_ID>
GROUP BY qcfd.flaw_name_level1, qcfd.flaw_name_level2 ORDER BY pcs DESC
```

---

## 第四步：采购 + PO级QC + 调拨 + FBA（全流程三单检查）

### 4.1 PO 级 QC 汇总
```sql
SELECT wr.purchase_order_id,
       MIN(wr.received_time::date) as first_rcpt, MAX(wr.received_time::date) as last_rcpt,
       COUNT(DISTINCT qc.id) as qc_cnt,
       SUM(CASE WHEN qc.check_type=1 THEN 1 ELSE 0 END) as full_check,
       SUM(CASE WHEN qc.check_type=0 THEN 1 ELSE 0 END) as sampling,
       SUM(CASE WHEN qc.quality_result=0 THEN 1 ELSE 0 END) as fail,
       SUM(CASE WHEN qc.quality_result=1 THEN 1 ELSE 0 END) as pass,
       SUM(qc.actual_check_total) as total_inspected
FROM plutus.warehouse_receipt wr
LEFT JOIN plutus.quality_check qc ON qc.warehouse_receipt_id=wr.id
WHERE wr.purchase_order_id IN (
  SELECT DISTINCT purchase_order_id FROM plutus.purchase_order_sku
  WHERE sku_code LIKE '<SPU_PREFIX>%'
) GROUP BY wr.purchase_order_id ORDER BY first_rcpt
```

### 4.2 PO 级缺陷明细
```sql
SELECT wr.purchase_order_id, qcfd.flaw_name_level1, qcfd.flaw_name_level2,
       SUM(qcfd.flaw_num) as pcs
FROM plutus.quality_check_flaw_detail qcfd
JOIN plutus.quality_check qc ON qcfd.quality_check_id=qc.id
JOIN plutus.warehouse_receipt wr ON qc.warehouse_receipt_id=wr.id
WHERE qcfd.spu_id=<PRODUCT_ID>
GROUP BY wr.purchase_order_id, qcfd.flaw_name_level1, qcfd.flaw_name_level2
ORDER BY wr.purchase_order_id, pcs DESC
```

### 4.3 调拨单（allocation plan）
```sql
SELECT ap.id, ap.from_warehouse_id, ap.to_warehouse_id, ap.status,
       ap.plan_ship_time, ap.add_time, ap.business_channel
FROM plutus.allocation_plan ap
JOIN plutus.allocation_plan_detail apd ON apd.allocation_plan_id=ap.id
JOIN plutus.sku_main sku ON apd.sku_id=sku.id
WHERE sku.spu_code='<SPU>' ORDER BY ap.add_time
```

### 4.4 FBA 发货
```sql
SELECT aiid.sku_code, COUNT(*) as batches, SUM(aiid.num) as total,
       MIN(aiid.add_time::date) as first, MAX(aiid.add_time::date) as last
FROM plutus.amazon_inbound_inbox_detail aiid
WHERE aiid.sku_code LIKE '<SPU_PREFIX>%'
GROUP BY aiid.sku_code ORDER BY total DESC
```

**报告中 PO 级表格必须列出：PO | 颜色 | 下单日 | 回货时间 | 全检/抽检 | QC次 | Fail | Pass | 检出缺陷（件数明细）**

---

## 第五步：销量·评分·退货·利润·库存

### 5.1 ⚠️ 销量去重
`amazon_product_performance_statement` 有多行：`ALL`/`FBA`/`FBM`。**只取 `fulfillment_channel='ALL'`**。

### 5.2 销量 + CVR + 退货
```sql
SELECT DATE_TRUNC('week', statement_date) as wk,
       SUM(sale_count::numeric) as sales, SUM(sessions::numeric) as sessions,
       ROUND(SUM(sale_count::numeric)/NULLIF(SUM(sessions::numeric),0)*100,2) as cvr,
       SUM((refund_count->>'actualValue')::numeric) as refunds,
       ROUND(SUM((refund_count->>'actualValue')::numeric)/NULLIF(SUM(sale_count::numeric),0)*100,2) as refund_rate
FROM plutus.amazon_product_performance_statement
WHERE asin IN (SELECT asin FROM plutus.amazon_catalog_item_relationship WHERE parent_asin='<PARENT_ASIN>')
  AND fulfillment_channel='ALL' AND shop_id='A1USBBMU2XLXD5'
GROUP BY wk ORDER BY wk
```

### 5.3 评分（务必拉取）
```sql
SELECT DATE_TRUNC('week', record_date) as wk,
       ROUND(AVG((payload->>'rate')::numeric),2) as rating
FROM plutus.amazon_product_rank_performance
WHERE asin IN (SELECT asin FROM plutus.amazon_catalog_item_relationship WHERE parent_asin='<PARENT_ASIN>')
GROUP BY wk ORDER BY wk
```

### 5.4 利润（从 amazon_profit_statement，非手算）
```sql
SELECT DATE_TRUNC('week', statement_date) as wk,
       SUM(item_price_amount) as revenue, SUM(avg_purchase_cost) as purchase,
       SUM(platform_cost) as platform, SUM(shipping_cost) as shipping,
       SUM(ads_cost) as ads, SUM(warehouse_storage_cost) as storage,
       SUM(refund_amount) as refunds
FROM plutus.amazon_profit_statement
WHERE shop_id='A1USBBMU2XLXD5' AND market_place_id='ATVPDKIKX0DER'
  AND asin IN (SELECT asin FROM plutus.amazon_catalog_item_relationship WHERE parent_asin='<PARENT_ASIN>')
GROUP BY wk ORDER BY wk
```
周利润 = revenue+purchase+platform+shipping+ads+storage+refunds。近50天退款未回填，报告注明。

### 5.5 库存
```sql
SELECT spu_code, SUM(fba_total_num) as fba, SUM(fba_sale_num) as avail,
       SUM(fba_reserved_num) as rsv, SUM(shipment_on_way_total_num) as on_way,
       SUM(master_station_now_available_num) as domestic
FROM plutus.amazon_fba_stock WHERE spu_code='<SPU>' GROUP BY spu_code
```
全链 = fba+on_way+domestic

---

## 第六步：ERP QC 盲区

ERP flaw_detail 只覆盖传统缺陷（车缝、尺寸、面料、辅料、后整），**不覆盖**：包装材料/印花工艺/辅料化学/特殊工艺/克重偏差/起球视觉效果。盲区类问题主动问用户是否有飞书记录。

---

## 第七步：运营确认

运营确认的缺陷对照 ERP flaw_detail 验证。如不在 ERP，报告明确标注"ERP 未覆盖"。

---

## 第八步：旧版 SPU + 跟单对比

检查同父 ASIN 下旧版 SPU 的供应商/通过率/跟单变化。

---

## 第九步：深层挖掘

1. 同 Listing 多次事故 2. 利润崩塌 3. QC 缺口（通过率 vs 退货率） 4. 供应商复用

---

## 第十步：飞书报告

### 固定结构
```
<callout> 核心结论 </callout>
一、销量·评分·退货率·利润·库存·时间线 合并总览（11列强制，第一章！）
二、运营确认
三、产品信息 + 跟单责任人
四、质检通过率
五、关键时期复盘：PO级QC（含全检/抽检+检出缺陷明细）+ 调拨 + FBA
六、供应商对比
七、根因分析
八、整肃方案
分析说明
```

### 合并总览表 11 列：周 | 销量 | Sessions | CVR | **评分** | 退货率 | **周利润** | **FBA** | **问题FBA** | **全链** | 事件

评分下降低于4.0标红↓，最低点标红↓↓↓。利润正绿负红。

---

## 关键陷阱

| 陷阱 | 错误 | 正确 |
|------|------|------|
| 销量 | 不过滤 channel | `fulfillment_channel='ALL'` |
| 通过率 | `quality_check.pass_rate` | `for_sale_num/receive_num` |
| 全检 | 以为只抽样11% | `check_type=1`=100%逐件检查 |
| 责任人 | 开发员负责供应商 | 跟单(purchase_uid)负责供应商选择 |
| BuyBox | 论证评分影响 | BuyBox=断货 |
| 利润 | cost_price 手算 | profit_statement.avg_purchase_cost 已换算USD |
| 利润时效 | 近50天当实际 | 退款未回填，需注明 |
| 评分 | 遗漏 | 必须拉取，共享ASIN注明混合影响 |
| 库存 | 遗漏 | 必须拉取 |
| 供应商 | `supplier` | 表名 `supplier1` |
| 报告顺序 | 产品信息放最前 | 合并总览第一章 |
| 合并表 | 缺列 | 11列全强制 |
| 调拨单 | 漏查 | 第三步三单全查 |
