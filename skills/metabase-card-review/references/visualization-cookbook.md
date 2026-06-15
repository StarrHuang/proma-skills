# Metabase 可视化配置常用配方

`visualization_settings` 是 card 的 JSON 配置，PUT 时必须保留+merge。

## 表格(table)条件格式

```python
vs['table.column_formatting'] = [
  # range 色带 (绿-白-红, 自动按 min/max 缩放)
  {'id': 1, 'type': 'range', 'columns': ['价差影响金额'],
   'colors': ['#88BF4D','#FFFFFF','#EF8C8C'],
   'min_type': None, 'max_type': None,
   'operator': '=', 'value': '', 'highlight_row': False},

  # single: 单值阈值上色
  {'id': 2, 'type': 'single', 'columns': ['amz阶梯/件'],
   'color': '#88BF4D', 'operator': '>', 'value': 0,
   'highlight_row': False},

  # single: >= 阈值
  {'id': 3, 'type': 'single', 'columns': ['amz一口价%'],
   'color': '#F9CF48', 'operator': '>=', 'value': 80,
   'highlight_row': False},
]
```

颜色参考：
- 红 `#EF8C8C`（警告/坏）
- 绿 `#88BF4D`（好/节省）
- 黄 `#F9CF48`（注意/中性）
- 白 `#FFFFFF`（range 中点）
- 蓝 `#509EE3`

operator 可用：`=, !=, <, >, <=, >=, is-null, not-null, contains`

## 列宽

```python
vs['table.column_widths'] = {
  '首图': 80,
  'SKC': 220,
  '信号': 200,
}
```

## 单列格式（column_settings）

key 必须是 JSON 字符串 `'["name","列名"]'`：

```python
vs['column_settings'] = {
  '["name","价差影响金额"]': {
    'number_style': 'currency', 'currency': 'USD',
    'currency_style': 'symbol', 'currency_in_header': False
  },
  '["name","溢价%"]': {
    'number_style': 'percent', 'scale': 0.01, 'decimals': 1
  },
  '["name","首图"]': {'view_as': 'image'},
  '["name","SPU"]': {
    'view_as': 'link',
    'link_url': 'https://erp.example.com/product/{{SPU}}'
  },
}
```

`view_as` 取值：
- `image` — 显示为图片
- `link` — 显示为链接（配 link_url 用 `{{列名}}` 插值）
- `auto` — 默认

`number_style` 取值：`decimal / percent / currency / scientific`

## 图表类型

### 瀑布图 (waterfall)
```python
d['display'] = 'waterfall'
vs['graph.dimensions'] = ['step']
vs['graph.metrics'] = ['value']
vs['waterfall.show_total'] = True
```

### 横向条形 (row)
```python
d['display'] = 'row'
vs['graph.dimensions'] = ['step']
vs['graph.metrics'] = ['qty']
```

### 组合图 (combo)
```python
d['display'] = 'combo'
vs['graph.dimensions'] = ['期间']
vs['graph.metrics'] = ['销量', 'GMV']  # 不同轴
vs['graph.y_axis.auto_split'] = True
```

### 透视表 (pivot)
表格里也可启用：
```python
vs['table.pivot'] = True
vs['table.pivot_column'] = '状态'
vs['table.cell_column'] = 'PO 数'
```

## 列重排 + 隐藏

```python
vs['table.columns'] = [
  {'name': 'SKC',  'enabled': True},
  {'name': 'SPU',  'enabled': False},  # 隐藏
  {'name': '信号', 'enabled': True},
]
```

## 仪表盘卡片调位置

dashcard 字段控制位置：
- `row, col`：网格坐标（24 列布局）
- `size_x, size_y`：宽高
- 同 `dashboard_tab_id` 内的 dashcard 不能重叠

典型 layout：
- 全宽：`col=0, size_x=24`
- 左右半：`col=0/12, size_x=12`
- 三列：`col=0/8/16, size_x=8`

## 信号叠加列（SQL 端做，不是可视化端）

```sql
TRIM(CONCAT_WS(' ',
  CASE WHEN <condA> THEN '🔴溢价' END,
  CASE WHEN <condB> THEN '✅阶梯' END,
  CASE WHEN <condC> THEN '🔒一口价' END
)) AS "信号"
```

emoji 信号词典（已用过的）：
- 🔴 红色警报（溢价/断货/大单无阶梯）
- 🟢 健康（低价/充足）
- 🟡 关注（紧缺<7d）
- 🟠 警告（断货-无补货）
- 🔵 中性
- ⚪ 持平/普通
- ✅ 正向（阶梯生效）
- 🔒 锁定（一口价）
- ⬆ 涨
- ⬇ 降
- ➡ 平稳
- ⚠ 数据异常
- ➖ 无对比

## 对比信息压缩列

不要 6 列分开放 amz/web 的 量/价/次数，合并成一列：

```sql
CONCAT_WS(' / ',
  'amz: ' || amz_q::text || '件@$' || amz_price::text || ' ×' || amz_cnt::text,
  'web: ' || web_q::text || '件@$' || web_price::text || ' ×' || web_cnt::text
) AS "采购计划(单次量@单价×次数)"
```
