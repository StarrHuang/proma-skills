---

## name: amazon-quality-investigation description: Amazon SPU 大货质量深度调查。当用户提到某个 SPU 编码 + 质量问题/评分下滑/销售异常/调样确认/差评/退货率异常/做工问题/质检/供应商问题 等关键词时触发。系统化拉取 ERP 质检、销量、评分、退货、采购、FBA发货数据，生成飞书文档分析报告。只要用户提及 SPU 且有质量或销售异常相关语境就应该使用此 skill。

# Amazon SPU 大货质量深度调查

## 前置要求

本 skill 依赖以下 MCP：`PostgreSQL` (plutus)、`metabase`、`sellersprite`（评分）、飞书 `lark-doc`。执行前先确认这些 MCP 已连接。

执行前必读：

- 飞书文档操作：读取 `skills/lark-doc/references/lark-doc-xml.md` 和 `skills/lark-doc/references/style/lark-doc-style.md`
- 飞书认证：读取 `skills/lark-shared/SKILL.md`

---

## 工作流总览

```
SPU 输入 → 基础信息 → 质检通过率 → QC 详情+缺陷 → 销量+评分+退货 → 
时间线串联 → 运营确认(如有) → 根因判定 → 飞书报告
```

在开始前先列出所有待执行的查询步骤给用户预览（`TaskCreate`），获得确认后并行执行独立查询。

---

## 第一步：获取 SPU 基础信息

### 1.1 产品与供应商

```sql
SELECT p.id, p.spu_code, p.supplier_id, s.supplier_name,
       p.develop_id, p.first_shelves_time, p.is_alive, p.status
FROM plutus.product p
LEFT JOIN plutus.supplier1 s ON p.supplier_id = s.id
WHERE p.spu_code = '<TARGET_SPU>'
```

### 1.2 SKU 清单与价格

```sql
SELECT sku_code, sale_price, cost_price, is_effective, first_shelves_time, skc_code
FROM plutus.sku_main WHERE spu_code = '<TARGET_SPU>' ORDER BY sku_code
```

### 1.3 ASIN 映射（通过 seller_sku → sku_code 关联）

```sql
SELECT acr.asin, acr.parent_asin, acr.seller_sku, acr.add_time
FROM plutus.amazon_catalog_item_relationship acr
WHERE acr.seller_sku IN (SELECT sku_code FROM plutus.sku_main WHERE spu_code = '<TARGET_SPU>')
ORDER BY acr.add_time
```

### 1.4 检查是否共享父 ASIN（排查优化前后 SPU 关系）

同一个 parent_asin 下可能有多个 SPU。如果存在，这可能是"优化迭代"关系，需要一并拉取旧版 SPU 的数据做对比。

```sql
SELECT DISTINCT sm.spu_code
FROM plutus.sku_main sm
JOIN plutus.amazon_catalog_item_relationship acr ON sm.sku_code = acr.seller_sku
WHERE acr.parent_asin = '<PARENT_ASIN>'
```

### 1.5 旧版 SPU 供应商（如果存在）

```sql
SELECT wr.supplier_id, s.supplier_name, COUNT(*) as receipt_count,
       SUM(wrs.receive_num) as total_recv, SUM(wrs.for_sale_num) as total_sale
FROM plutus.warehouse_receipt wr
JOIN plutus.warehouse_receipt_sku wrs ON wrs.warehouse_receipt_id = wr.id
JOIN plutus.sku_main sku ON wrs.sku_id = sku.id
LEFT JOIN plutus.supplier1 s ON wr.supplier_id = s.id
WHERE wr.received_time IS NOT NULL AND sku.spu_code = '<OLD_SPU>'
GROUP BY wr.supplier_id, s.supplier_name
```

---

## 第二步：质检通过率（正确公式）

**⚠️ 通过率 ≠ quality_check.pass_rate。正确公式：**

```sql
SELECT sku.spu_code, wr.supplier_id, s.supplier_name,
       COUNT(*) as receipt_count,
       SUM(wrs.receive_num) as total_receive,
       SUM(wrs.for_sale_num) as total_for_sale,
       ROUND(SUM(wrs.for_sale_num)::numeric / NULLIF(SUM(wrs.receive_num), 0) * 100, 2) as pass_rate_pct,
       SUM(wrs.no_pass_num) as no_pass,
       SUM(wrs.refine_num) as to_refine
FROM plutus.warehouse_receipt wr
INNER JOIN plutus.warehouse_receipt_sku wrs ON wrs.warehouse_receipt_id = wr.id
INNER JOIN plutus.sku_main sku ON wrs.sku_id = sku.id
LEFT JOIN plutus.supplier1 s ON wr.supplier_id = s.id
WHERE wr.received_time IS NOT NULL AND sku.spu_code = '<TARGET_SPU>'
GROUP BY sku.spu_code, wr.supplier_id, s.supplier_name
ORDER BY receipt_count DESC
```

**字段含义：**

- 收货量 = `receive_num`（仓库实际收到件数）
- 通过率 = `for_sale_num / receive_num`
- 不合格 = `no_pass_num`（直接判定不合格、未送修）
- 送返修 = `refine_num`（有问题但可修）

---

## 第三步：QC 逐批详情与缺陷明细

### 3.1 QC 方式（全检/抽检）与合格率

```sql
SELECT qc.check_type, COUNT(*) as cnt,
       ROUND(AVG(qc.check_total),1) as avg_check_num,
       ROUND(AVG(qc.actual_check_total),1) as avg_batch_size
FROM plutus.quality_check qc
JOIN plutus.warehouse_receipt wr ON qc.warehouse_receipt_id = wr.id
WHERE wr.purchase_order_id IN (
  SELECT DISTINCT purchase_order_id FROM plutus.purchase_order_sku
  WHERE sku_code LIKE '<TARGET_SPU_PREFIX>%'
) GROUP BY qc.check_type
```

- `check_type=1` = 全检（每批都查，但每批抽样率仅 \~11%）
- `check_type=0` = 抽检

### 3.2 缺陷明细（抓大类+子类+件数）

```sql
SELECT qcfd.flaw_name_level1, qcfd.flaw_name_level2,
       COUNT(*) as occur_count, SUM(qcfd.flaw_num) as total_pcs
FROM plutus.quality_check_flaw_detail qcfd
WHERE qcfd.spu_id = <PRODUCT_ID>
GROUP BY qcfd.flaw_name_level1, qcfd.flaw_name_level2
ORDER BY total_pcs DESC
```

### 3.3 缺陷按 PO 拆分（用于定位具体批次问题）

```sql
SELECT wr.purchase_order_id,
       qcfd.flaw_name_level1, qcfd.flaw_name_level2,
       SUM(qcfd.flaw_num) as pcs
FROM plutus.quality_check_flaw_detail qcfd
JOIN plutus.quality_check qc ON qcfd.quality_check_id = qc.id
JOIN plutus.warehouse_receipt wr ON qc.warehouse_receipt_id = wr.id
WHERE qcfd.spu_id = <PRODUCT_ID>
GROUP BY wr.purchase_order_id, qcfd.flaw_name_level1, qcfd.flaw_name_level2
ORDER BY wr.purchase_order_id, pcs DESC
```

---

## 第四步：采购+质检+FBA 发货时间线

### 4.1 采购单

```sql
SELECT purchase_order_id, sku_code, num, price, delivered_num, add_time::date
FROM plutus.purchase_order_sku
WHERE sku_code LIKE '<TARGET_SPU_PREFIX>%'
ORDER BY add_time
```

### 4.2 按 PO 汇总质检结果（关键！）

```sql
SELECT wr.purchase_order_id,
       MIN(wr.received_time::date) as first_receipt,
       MAX(wr.received_time::date) as last_receipt,
       COUNT(DISTINCT qc.id) as qc_count,
       SUM(CASE WHEN qc.quality_result=0 THEN 1 ELSE 0 END) as fail_count,
       SUM(CASE WHEN qc.quality_result=1 THEN 1 ELSE 0 END) as pass_count,
       SUM(qc.check_total) as total_sampled,
       SUM(qc.actual_check_total) as total_batch,
       ROUND(SUM(qc.check_total)::numeric / NULLIF(SUM(qc.actual_check_total),0)*100,1) as sample_pct
FROM plutus.warehouse_receipt wr
LEFT JOIN plutus.quality_check qc ON qc.warehouse_receipt_id = wr.id
WHERE wr.purchase_order_id IN (
  SELECT DISTINCT purchase_order_id FROM plutus.purchase_order_sku
  WHERE sku_code LIKE '<TARGET_SPU_PREFIX>%'
)
GROUP BY wr.purchase_order_id ORDER BY first_receipt
```

- `quality_result=0` = 不合格，`quality_result=1` = 合格
- `total_sampled` = 抽检总件数，`total_batch` = 批次总件数

### 4.3 FBA 发货

```sql
SELECT aiid.sku_code, COUNT(*) as batches, SUM(aiid.num) as total,
       MIN(aiid.add_time::date) as first, MAX(aiid.add_time::date) as last
FROM plutus.amazon_inbound_inbox_detail aiid
WHERE aiid.sku_code LIKE '<TARGET_SPU_PREFIX>%'
GROUP BY aiid.sku_code ORDER BY total DESC
```

---

## 第五步：销量 · 评分 · 退货率

### 5.1 ⚠️ 销量去重规则

`amazon_product_performance_statement` 表中同一天同 ASIN 有多行：`ALL`（汇总行）、`FBA`、`FBM`。**必须只取** `fulfillment_channel = 'ALL'`，否则销量翻 2-3 倍。

### 5.2 销量 + Sessions + CVR + 退货率（US 站）

```sql
SELECT DATE_TRUNC('week', statement_date) as week,
       SUM(sale_count::numeric) as sales,
       SUM(sale_amount::numeric) as revenue,
       SUM(sessions::numeric) as sessions,
       ROUND(SUM(sale_count::numeric)/NULLIF(SUM(sessions::numeric),0)*100,2) as cvr_pct,
       SUM((refund_count->>'actualValue')::numeric) as refunds,
       ROUND(SUM((refund_count->>'actualValue')::numeric)/NULLIF(SUM(sale_count::numeric),0)*100,2) as refund_rate
FROM plutus.amazon_product_performance_statement
WHERE asin IN (SELECT asin FROM plutus.amazon_catalog_item_relationship WHERE parent_asin = '<PARENT_ASIN>')
  AND fulfillment_channel = 'ALL'
  AND shop_id = 'A1USBBMU2XLXD5'
GROUP BY DATE_TRUNC('week', statement_date)
ORDER BY week
```

### 5.3 评分趋势

```sql
SELECT DATE_TRUNC('week', record_date) as week,
       ROUND(AVG((payload->>'rate')::numeric),2) as avg_rating,
       COUNT(DISTINCT asin) as asin_count
FROM plutus.amazon_product_rank_performance
WHERE asin IN (SELECT asin FROM plutus.amazon_catalog_item_relationship WHERE parent_asin = '<PARENT_ASIN>')
GROUP BY DATE_TRUNC('week', record_date) ORDER BY week
```

### 5.4 ⚠️ 重要注意事项

- **BuyBox 波动由断货导致，与评分无关。不要用 BuyBox 变化论证评分影响。**
- 销量判断评分影响：看 CVR（转化率）和 Sessions（流量）是否持续下降
- 如果 CVR 上升但售价大幅下降（清仓价），要注明折扣可能掩盖了真实品质信号
- 如果需要在报告中展示日销峰值，可以单独查每日数据：`GROUP BY statement_date::date`

---

## 第六步：运营确认（如有）

用户可能提供运营手工试衣/调样确认的具体缺陷描述（如"肩宽、袖笼、下摆抽褶左右不一致"）。将这些缺陷与 ERP 的 flaw_detail 中的「车缝-起扭/打褶」「车缝-不对称/高低/太小」等条目做对照，验证 ERP 记录和实物发现是否吻合。

---

## 第七步：检查旧版 SPU 供应商链

如果存在"优化前后"关系，需要对比两个版本的供应商变化：

- 旧版有多少家供应商？各自的通过率？
- 新版是否砍掉了通过率最高的供应商？
- 新版是否集中到了通过率最低的供应商？

---

## 第八步：生成飞书文档分析报告

### 报告结构（固定模板）

```
<title>[SPU] 质量根因分析报告</title>

<callout>核心结论：一句话概括问题、根因、影响、关键数据</callout>

一、销量·评分·退货率·时间线 合并总览
  - 一张大表：周 | 日销峰值 | 周销 | CVR | 评分 | 退货率 | Sessions | 关键事件
  - callout：评分-销量因果链分析

二、运营试衣确认（如有）
  - 表格列出 SKU + 缺陷描述

三、产品基本信息
  - 优化前 vs 优化后 对比表（如果存在旧版）

四、质检通过率
  - 新版 + 旧版供应商级通过率对比表
  - 说明劣化了多少个百分点

五、关键时期复盘（PO 级 QC 详情）
  - QC 方式说明（全检/抽检 + 抽样率）
  - 检出缺陷明细表
  - PO 级表格：PO | 颜色 | 下单日 | 最早回货 | 最晚回货 | QC次 | Fail | Pass | 抽检率 | 检出缺陷
  - callout：缺陷与运营试衣对照
  - 同期 FBA 发货（零拦截）
  - 综合判定

六、供应商对比
  - 表格 + callout 根因定位

七、根因分析
  - #1 优化/供应商方向错误
  - #2 供应商身份/注册问题
  - #3 QC 覆盖率 + 三方脱节
  - #4 评分跌破阈值 → 失去 Deal 资格
  - #5 供应商管理体系漏洞

八、整肃方案
  - 短期 callout（本周：核查供应商、约谈责任人）
  - 中期 callout（本月：系统阻断、黑名单、全量回溯）
  - 长期 callout（仪表板、健康度监控、KPI绑定）

分析说明 callout：
  - 评分口径、质检通过率口径、QC不合格率口径、销量口径、BuyBox说明、数据来源、分析日期
```

### 文档创建与更新

- 用 `lark-cli docs +create --api-version v2 --content '<xml>'` 创建
- 内容较长时分段用 `--command append` 追加
- 需先读取 `skills/lark-doc/references/lark-doc-xml.md` 了解 XML 语法
- 需先读取 `skills/lark-doc/references/style/lark-doc-style.md` 了解样式规则
- 颜色语义：红色=风险/警告，绿色=正常/推荐，黄色=注意/待确认

---

## 关键陷阱（必须遵守）

| 陷阱 | 错误做法 | 正确做法 |
| --- | --- | --- |
| 销量翻倍 | 不过滤 fulfillment_channel | 只取 `fulfillment_channel='ALL'` |
| QC 通过率造假 | 用 `quality_check.pass_rate` 字段 | 用 `for_sale_num / receive_num` |
| BuyBox 误读 | 用 BuyBox 变化代表评分变化 | BuyBox 由断货导致，不纳入评分分析 |
| 供应商主表 | `supplier` | 正确表名是 `supplier1` |
| ASIN 映射 | 直接关联 spu_code | 需通过 `seller_sku → sku_main.sku_code → spu_code` |
| 产品字段 | 假设字段存在 | 先用 `information_schema.columns` 查字段结构 |
| QC 检验方式 | 以为"全检"=每件都查 | check_type=1 "全检" 只是每批都查，抽样率约 11% |
| 旧版 SPU | 忽略优化迭代关系 | 检查 parent_asin 下是否有多个 SPU |
