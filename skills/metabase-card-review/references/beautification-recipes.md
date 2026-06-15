# Metabase 表格美化配方库

> 当 card 列数 ≥ 12 时启动美化。所有配方都来自真实落地的产供销看板（188），可直接复用。

## 美化原则（不可违反）

1. **隐藏不删除原始列**：所有用于驱动可视化/被合并/被排序依赖的原始数字列，在 `table.columns` 里设 `enabled: false`。运营下载 xlsx 时仍能拿到完整数据。
2. **emoji + 文字 → 1 列代替 N 列**：把"层级 + 状态 + 颜色"合并到一个文本列。
3. **CONCAT_WS 跳过 NULL**：分隔符 + NULL 安全的拼接，不会出现 `· ·` 双分隔符。
4. **列宽显式设定**：合并列宽 140-260，数字列 80-110，名称列 100-220。
5. **条件格式按"决策重要性"上色**：救火列（紧急分/可售天数）必有色带；金额列可选。

---

## 配方 1：行动建议（优先级 + 行动）合一

适用于：所有"任务清单"型 card（紧急清单、待办、风险列表）

```sql
CASE
  WHEN <P0 条件> THEN '🔴 P0 紧急补采'
  WHEN <P1 条件A> THEN '🟠 P1 催 FBA 接收'
  WHEN <P1 条件B> THEN '🟠 P1 跟踪货件'
  WHEN <P2 条件A> THEN '🟡 P2 预防性采购'
  WHEN <P2 条件B> THEN '🟢 P2 有缓冲'
  ELSE '⚪ 健康'
END AS "行动建议"
```

emoji 优先级：🔴 P0 > 🟠 P1 > 🟡 P2 > 🟢 P2 > ⚪ 健康

---

## 配方 2：可售天数 + 状态色

适用于：所有"天数"类指标（FBA 可售/全链/SKC 可售）

```sql
CASE
  WHEN <days> IS NULL THEN '-'
  WHEN <days> = 0     THEN '🔴 断货'
  WHEN <days> <= 7    THEN '🔴 ' || ROUND(<days>, 1) || 'd'
  WHEN <days> <= 14   THEN '🟠 ' || ROUND(<days>, 1) || 'd'
  WHEN <days> <= 30   THEN '🟡 ' || ROUND(<days>, 1) || 'd'
  ELSE                     '🟢 ' || ROUND(<days>, 1) || 'd'
END AS "FBA 可售"
```

阈值来源：`amazon_inventory_thresholds` KV 表（FBA_DAYS_CRITICAL=7/WARNING=14/OK=20）

同时要 **隐藏原始数字列** `fba_days_num`（enabled: false），保留供下载和排序用。

---

## 配方 3：SPU 等级（爆 / 热 / 普）emoji 标签

```sql
CASE <tier>
  WHEN '爆品' THEN '🔥 爆品'
  WHEN '热销' THEN '🔶 热销'
  WHEN '普通' THEN '🔹 普通'
  ELSE             '⚪ 滞销'
END AS "层级"
```

或合并到状态列（多信号叠加）：
```sql
CONCAT_WS(' ',
  <状态 emoji+文字>,
  CASE WHEN daily >= 100 THEN '🔥'
       WHEN daily >= 30  THEN '🔶'
       WHEN daily >= 3   THEN '🔹'
       ELSE '⚪' END
) AS "状态"
```

---

## 配方 4：库存分布（多仓 → 1 列短文本）

适用于：把 FBA/在途/采购/国内/美西 多个数字列合并

```sql
CONCAT_WS(' · ',
  CASE WHEN fba_stock > 0       THEN 'FBA ' || fba_stock::text END,
  CASE WHEN fba_inflight > 0    THEN '在途 ' || fba_inflight::text END,
  CASE WHEN purchase_on_way > 0 THEN '采购 ' || purchase_on_way::text END,
  CASE WHEN cn_warehouse > 0    THEN '国内 ' || cn_warehouse::text END,
  CASE WHEN la_stock > 0        THEN '美西 ' || la_stock::text END
) AS "库存分布"
```

每段都用 `CASE WHEN X > 0 THEN ... END` 包起来——0 不显示。
分隔符用 `·`（中点），视觉比逗号轻。

---

## 配方 5：FBA 在途时效拆分（互斥三档）

```sql
CONCAT_WS(' · ',
  CASE WHEN fba_7d      > 0 THEN '7d '    || fba_7d::text END,
  CASE WHEN fba_8_21d   > 0 THEN '8-21d ' || fba_8_21d::text END,
  CASE WHEN fba_22d_plus> 0 THEN '22d+ '  || fba_22d_plus::text END
) AS "FBA 在途"
```

SQL 计算互斥桶的方式见 known-pitfalls.md（`shipment_on_way_total ≠ f7+f14+f21`）。

---

## 配方 6：数量进度（采购单 已交 / 待交）

```sql
CONCAT_WS(' · ',
  SUM(num)::text || ' 单',
  CASE WHEN SUM(delivered) > 0
       THEN '已交 ' || SUM(delivered)::text END,
  CASE WHEN SUM(num) - SUM(delivered) > 0
       THEN '🟡 待交 ' || (SUM(num) - SUM(delivered))::text END
) AS "数量进度"
```

---

## 配方 7：时间节点链路（多个时间戳 → 箭头连）

```sql
CONCAT_WS(' → ',
  '下单 ' || TO_CHAR(add_time, 'MM-DD'),
  CASE WHEN supplier_receive_time IS NOT NULL
       THEN '接单 ' || TO_CHAR(supplier_receive_time, 'MM-DD') END,
  CASE WHEN full_size_receive_time IS NOT NULL
       THEN '全尺 ' || TO_CHAR(full_size_receive_time, 'MM-DD') END,
  CASE WHEN completed_time IS NOT NULL
       THEN '完成 ' || TO_CHAR(completed_time, 'MM-DD') END
) AS "节点"
```

未达节点不显示；分隔符 `→` 表示流程顺序。

`MM-DD` 比 `YYYY-MM-DD` 短；如有跨年场景用 `MM/DD/YY`。

---

## 配方 8：状态 + 逾期合一

```sql
CONCAT_WS(' ',
  CASE status
    WHEN 0 THEN '🟡 待确认'
    WHEN 1 THEN '🟢 生产中'
    WHEN 2 THEN '⚪ 已完成'
    WHEN 3 THEN '⚫ 已取消'
  END,
  CASE WHEN status IN (0,1) AND COALESCE(expected, deadline) < NOW()
       THEN '🔴 逾期 ' || EXTRACT(DAY FROM (NOW() - COALESCE(expected, deadline)))::int || 'd'
  END
) AS "状态"
```

---

## 配方 9：标签合一（多个 boolean → emoji 串）

```sql
CONCAT_WS(' ',
  CASE WHEN 'amz单独补货' = ANY(tag)   THEN '🛒 amz' END,
  CASE WHEN '库存危险sku' = ANY(tag)   THEN '⚠ 危险' END,
  CASE WHEN '首次返单'    = ANY(tag)   THEN '🆕 首返' END
) AS "标签"
```

---

## 配方 10：amz vs web 对比压缩

```sql
CONCAT_WS(' / ',
  'amz: ' || COALESCE(amz_qty::text, '-') || '件@$' || COALESCE(amz_price::text, '-') || ' ×' || COALESCE(amz_cnt::text, '0'),
  'web: ' || COALESCE(web_qty::text, '-') || '件@$' || COALESCE(web_price::text, '-') || ' ×' || COALESCE(web_cnt::text, '0')
) AS "采购计划(单次量@单价×次数)"
```

---

## 配方 11：多信号叠加（横向 + 阶梯 + 一口价 + 异动）

```sql
TRIM(CONCAT_WS(' ',
  CASE WHEN <横向价格判定> THEN '🔴溢价' WHEN ... END,
  CASE WHEN <阶梯生效>     THEN '✅阶梯' WHEN ... END,
  CASE WHEN <一口价占比>   THEN '🔒一口价' END,
  CASE WHEN <异动>         THEN '⬆涨' WHEN ... END
)) AS "信号"
```

每个 emoji 对应一个独立判定，可同时出现。

---

## 配方 12：SKC/SKU 断货分层

```sql
CASE
  WHEN sto_skc = 0 AND sto = 0 THEN '0'
  WHEN sto_skc > 0 THEN '🔴 ' || sto_skc::text || ' SKC · ' || sto::text || ' SKU'
  ELSE sto::text || ' SKU'
END AS "断货 SKC/SKU"
```

或更详细：
```sql
CONCAT_WS(' · ',
  CASE
    WHEN sto_sku_cnt = sku_cnt AND sku_cnt > 0 THEN '🔴 SKC 全断'
    WHEN sto_sku_cnt > 0 THEN '🟠 SKC 部分断'
  END,
  sku_cnt::text || '总',
  CASE WHEN sto_sku_cnt > 0 THEN sto_sku_cnt::text || '断' END,
  CASE WHEN risk_sku_cnt > 0 THEN risk_sku_cnt::text || '紧' END
) AS "SKC/SKU 断货"
```

---

## 配方 13：行级背景染色（断货 / 恢复 / 持续）

适用于：本身只有 3-5 行的"汇总"型 card（断货 GMV、PO 状态汇总）

```python
vs['table.column_formatting'] = [
  {'id':1,'type':'single','columns':['类型'],'color':'#EF8C8C',
   'operator':'contains','value':'损失','highlight_row':True},
  {'id':2,'type':'single','columns':['类型'],'color':'#88BF4D',
   'operator':'contains','value':'恢复','highlight_row':True},
  {'id':3,'type':'single','columns':['类型'],'color':'#F9CF48',
   'operator':'contains','value':'持续','highlight_row':True},
]
```

`highlight_row: True` 是整行染色的关键。

---

## 配方 14：紧急分 / 占比% mini-bar 色带

```python
vs['table.column_formatting'] = [
  {'id':1,'type':'range','columns':['紧急分'],
   'colors':['#FFFFFF','#EF8C8C'],
   'min_type':'custom','min_value':0,
   'max_type':'custom','max_value':100,
   'value':'','operator':'=','highlight_row':False}
]
```

- 2 色（白→红）：单极指标（越大越紧急/越多越坏）
- 3 色（红→白→绿）：双极指标（可售天数：少坏多好）

---

## 配方 15：PO 周龄热力 → 改 pivot 表

适用于：行=维度A、列=维度B、值=指标的 2D 分布

```python
d['display'] = 'pivot'
vs = {
  'pivot_table.column_split': {
    'rows':    [['field-literal', '下单龄段', 'type/Text']],
    'columns': [['field-literal', '状态',     'type/Text']],
    'values':  [['aggregation', 0]]
  },
  'pivot.show_column_totals': True,
  'pivot.show_row_totals': True,
  'table.column_formatting': [
    {'columns':['PO 数'],'value':'','type':'range',
     'colors':['#FFFFFF','#EF8C8C'],
     'min_type':'min','max_type':'max',
     'operator':'=','highlight_row':False,'id':1}
  ]
}
```

`min_type: 'min'` + `max_type: 'max'` 表示自动按当前数据范围缩放色带。

---

## 配方 16：导出友好的 table.columns 配置

```python
vs['table.columns'] = [
  # 展示列(精简)
  {'name': '首图',         'enabled': True},
  {'name': 'SPU',          'enabled': True},
  {'name': '行动建议',     'enabled': True},
  {'name': 'FBA 可售天数', 'enabled': True},
  {'name': '库存分布',     'enabled': True},
  # 导出友好(隐藏但下载时有)
  {'name': 'fba_days_num',   'enabled': False},
  {'name': 'chain_days_num', 'enabled': False},
  {'name': 'fba_qty',        'enabled': False},
  {'name': 'fc_qty',         'enabled': False},
  {'name': 'shipment_qty',   'enabled': False},
  {'name': 'allocation_qty', 'enabled': False},
  {'name': 'cn_qty',         'enabled': False},
  {'name': 'la_qty',         'enabled': False},
  {'name': 'purchase_qty',   'enabled': False},
]
```

**关键**：SQL 里要 SELECT 出这些原始列（带 snake_case 别名），UI 把它们隐藏。下载时全部保留。

---

## 美化检查清单

完成一张表格美化前过一遍：

- [ ] 列数 ≤ 11（视野舒适上限）
- [ ] 主指标列有 emoji + 颜色码
- [ ] 数字列有合适的色带或单位
- [ ] 时间列用 `MM-DD` 短格式
- [ ] 多状态合一（不要 6 列布尔）
- [ ] 多仓库存合一
- [ ] 原始数字列保留但 `enabled: false`
- [ ] 列宽显式设定（避免自动列宽撕裂）
- [ ] 首图列 `view_as: image`
- [ ] 货币列 `currency: USD`，百分比列 `percent + scale: 0.01`
- [ ] 看板预览过一遍：移动端能看清吗？

---

## 反模式

- ❌ 把所有列都加 emoji（视觉污染，重要 ≠ 不重要的失去对比）
- ❌ 直接 DROP 原始数字列（运营要导出 xlsx 给财务）
- ❌ 在 SQL 里写死阈值（应该 JOIN amazon_inventory_thresholds 让运营可调）
- ❌ pivot 表用在多维数据（pivot 只适合 2D 分布）
- ❌ `highlight_row: True` 用在大表（每行都染色就是没染色）
