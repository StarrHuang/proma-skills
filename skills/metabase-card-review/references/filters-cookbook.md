# Metabase 看板筛选项配方库

> 给看板加"店铺/市场/SPU/SKC/时间..."等筛选项，让运营点几下就能定位数据。所有配方来自真实落地（188、197 看板）。

## 三层架构

筛选项的完整工程涉及三层，**任何一层缺失都会导致筛选不生效**：

```
1. 单卡 SQL：定义 template-tag（占位符 + 默认值 + required）
2. Dashboard：顶部 parameter + values_source 配置（决定 UI 是下拉/搜索）
3. 桥接层：每张 dashcard 的 parameter_mappings 把顶部参数路由到卡内 template-tag
```

漏一层的典型症状：
- 缺第 1 层：SQL 跑不出筛选效果，整张卡报错或返回全量
- 缺第 2 层：filter 是文本框输入 ID，用户骂"这破东西怎么用"
- 缺第 3 层：dashboard 顶部改了参数，但 card 不响应

---

## Step 1 — 单卡 SQL 加 template-tag

### 1.1 基本占位符（required + default）

```sql
WHERE 1=1
  [[ AND shop_id = {{shop_id}} ]]
```

template-tags 配置（在 `dataset_query.native.template-tags`）：

```python
"template-tags": {
  "shop_id": {
    "id": "<uuid>",  # 任意 uuid
    "name": "shop_id",
    "display-name": "店铺",
    "type": "text",
    "default": "A1USBBMU2XLXD5",
    "required": True   # ⚠️ 关键: question 直链不会应用 default, 必须设 true
  }
}
```

### 1.2 中文名翻译回 ID（推荐）

让用户输入"美国"而不是 `ATVPDKIKX0DER`，SQL 内部用 lookup 表翻译：

```sql
WHERE 1=1
  [[ AND shop_id IN (
       SELECT item_code FROM plutus.code_library
       WHERE code_type='AMAZON_SHOP_ID_NAME_MAPPING'
       AND item_value = {{shop_name}}
     ) ]]
  [[ AND market_place_id IN (
       SELECT item_code FROM plutus.code_library
       WHERE code_type='AMAZON_MARKPLACE_ID_NAME_MAPPING'
       AND item_value = {{marketplace_name}}
     ) ]]
```

template-tags：

```python
{
  "shop_name": {
    "id": "<uuid>", "name": "shop_name",
    "display-name": "店铺", "type": "text",
    "default": "香港主体店铺(北美)",
    "required": True
  },
  "marketplace_name": {
    "id": "<uuid>", "name": "marketplace_name",
    "display-name": "市场", "type": "text",
    "default": "美国",
    "required": True
  }
}
```

> 前提：业务库里有字典表（如 `code_library` 用 `code_type` + `item_code` + `item_value`）。如果没有，建一张静态字典 view，或用 CASE WHEN 兜底。

### 1.3 多键 OR 解析（用户填任一筛选项都生效）

适合"Parent ASIN / Cider SPU / SKC / Cider SKU / Child ASIN / MSKU 任填一个就能定位"的钻取卡：

```sql
WITH asin_universe AS (
  SELECT DISTINCT cir.parent_asin, cir.asin, cir.shop_id, cir.market_place_id,
                  acm.cider_sku, sm.skc_code, sm.spu_code
  FROM plutus.amazon_catalog_item_relationship cir
  LEFT JOIN plutus.amazon_code_mapping acm
       ON acm.asin = cir.asin AND acm.shop_id = cir.shop_id
       AND acm.market_place_id = cir.market_place_id AND acm.is_newest = true
  LEFT JOIN plutus.sku_main sm ON sm.sku_code = acm.cider_sku
  WHERE 1=1
    [[ AND cir.parent_asin = {{parent_asin}} ]]
    [[ AND cir.asin = {{child_asin}} ]]
    [[ AND cir.seller_sku = {{msku}} ]]
    [[ AND sm.spu_code = {{cider_spu}} ]]
    [[ AND sm.skc_code = {{skc}} ]]
    [[ AND sm.sku_code = {{cider_sku}} ]]
)
SELECT ... FROM ... WHERE asin IN (SELECT asin FROM asin_universe);
```

任填一个 → 解析成 child_asin 集合 → 主查询用集合过滤。

---

## Step 2 — Dashboard 顶部参数（决定 UI）

### 2.1 下拉（数量少 ≤ 20）— lookup card 作为数据源

**先建 lookup card**（存到 collection，跟看板分开）：

```sql
-- card 1697: 店铺名 lookup
SELECT item_value AS 店铺
FROM plutus.code_library
WHERE code_type='AMAZON_SHOP_ID_NAME_MAPPING' AND enabled=true
ORDER BY item_value
```

**dashboard parameter 配置**：

```python
{
  "slug": "shop_name",
  "name": "店铺",
  "type": "category",
  "sectionId": "string",
  "values_query_type": "list",      # ⚠️ list = 下拉
  "values_source_type": "card",     # 数据源类型
  "values_source_config": {
    "card_id": 1697,                # lookup card id
    "value_field": ["field", "店铺", {"base-type": "type/Text"}]
  },
  "default": "香港主体店铺(北美)",
  "required": True,
  "id": "<uuid>"
}
```

UI 表现：点开是下拉列表（4 个店铺名直接选）。

### 2.2 输入时搜索匹配（数量大）

适合 parent_asin (~5000)、cider_spu (~10000)、SKC (~50000) 这种百万级维度：

```sql
-- card 1699: parent_asin lookup
SELECT DISTINCT parent_asin
FROM plutus.amazon_catalog_item_relationship
WHERE parent_asin IS NOT NULL
ORDER BY parent_asin LIMIT 5000
```

```python
{
  "slug": "parent_asin",
  "name": "Parent ASIN",
  "type": "category",
  "sectionId": "string",
  "values_query_type": "search",    # ⚠️ search = 输入时搜
  "values_source_type": "card",
  "values_source_config": {
    "card_id": 1699,
    "value_field": ["field", "parent_asin", {"base-type": "type/Text"}]
  },
  "id": "<uuid>"
}
```

UI 表现：文本框，输入 `B0CWK` 自动匹配 `B0CWK2YJTR / B0CWKL... / ...`。

### 2.3 时间筛选

```python
{
  "slug": "start_date",
  "name": "开始日期",
  "type": "date/all-options",   # 提供 各种日期 widget(单日/区间/相对/快捷)
  "sectionId": "date",
  "id": "<uuid>"
}
```

`date/all-options` 是最灵活的，包括"过去 7 天/本月/上季度"等快捷选项。

### 2.4 时间粒度（自定义枚举）

```python
{
  "slug": "granularity",
  "name": "时间粒度",
  "type": "category",
  "sectionId": "string",
  "default": "week",
  "id": "<uuid>"
}
```

SQL 端用 `DATE_TRUNC({{granularity}}, statement_date)` 应用。

---

## Step 3 — 桥接层 parameter_mappings（最容易漏！）

dashboard 顶部 parameter 和 card 内 template-tag 是**两套独立 ID**，必须在每张 dashcard 的 `parameter_mappings` 里手动桥接：

```python
dashcard['parameter_mappings'] = [
  {
    "parameter_id": "<dashboard parameter 的 uuid, 见 Step 2>",
    "card_id": 1666,
    "target": ["variable", ["template-tag", "shop_name"]]
  },
  {
    "parameter_id": "<另一个 parameter uuid>",
    "card_id": 1666,
    "target": ["variable", ["template-tag", "marketplace_name"]]
  }
]
```

⚠️ **每张 dashcard 都要单独写 parameter_mappings**。PUT `/api/dashboard/<id>` 时一起提交。

---

## 完整工作流（一次性配齐 11 个筛选 × 16 张卡）

```python
import json, urllib.request, uuid
API='https://metabase.shopcider.cn'; KEY='<key>'

# 1. 建 lookup cards（数量少用下拉, 数量大也建 card 但用 search）
lookup_configs = [
  ('店铺名 (下拉)',      "SELECT item_value AS 店铺 FROM plutus.code_library WHERE code_type='AMAZON_SHOP_ID_NAME_MAPPING' ORDER BY 1", '店铺'),
  ('市场名 (下拉)',      "SELECT item_value AS 市场 FROM plutus.code_library WHERE code_type='AMAZON_MARKPLACE_ID_NAME_MAPPING' ORDER BY 1", '市场'),
  ('parent_asin (搜索)', "SELECT DISTINCT parent_asin FROM plutus.amazon_catalog_item_relationship WHERE parent_asin IS NOT NULL ORDER BY 1 LIMIT 5000", 'parent_asin'),
  ('cider_spu (搜索)',   "SELECT DISTINCT spu_code FROM plutus.sku_main WHERE spu_code IS NOT NULL ORDER BY 1 LIMIT 10000", 'spu_code'),
  # ... skc / sku / child_asin / msku
]

lookup_ids = {}
for name, sql, col in lookup_configs:
  payload = {
    'name': f'[LOOKUP] {name}',
    'display': 'table',
    'description': f'供 dashboard filter 使用的 lookup card',
    'visualization_settings': {},
    'collection_id': <your_collection>,
    'dataset_query': {'database': 14, 'type': 'native', 'native': {'query': sql}}
  }
  req = urllib.request.Request(f'{API}/api/card', data=json.dumps(payload).encode(),
    method='POST', headers={'x-api-key': KEY, 'Content-Type': 'application/json'})
  r = json.load(urllib.request.urlopen(req, timeout=60))
  lookup_ids[name] = (r['id'], col)

# 2. 为每张目标 card 设 template-tags + required=true
for card_id, tags in card_tag_map.items():
  req = urllib.request.Request(f'{API}/api/card/{card_id}', headers={'x-api-key':KEY})
  d = json.load(urllib.request.urlopen(req, timeout=30))
  d['dataset_query']['native']['template-tags'] = tags  # see Step 1
  # PUT 时必须带完整 payload
  payload = {
    'dataset_query': d['dataset_query'], 'display': d['display'],
    'visualization_settings': d.get('visualization_settings') or {},
    'name': d['name'], 'description': d.get('description'),
    'parameters': d.get('parameters') or [],
  }
  urllib.request.urlopen(urllib.request.Request(f'{API}/api/card/{card_id}',
    data=json.dumps(payload).encode(), method='PUT',
    headers={'x-api-key':KEY,'Content-Type':'application/json'}), timeout=30)

# 3. 设 dashboard parameters + parameter_mappings(每张 dashcard)
req = urllib.request.Request(f'{API}/api/dashboard/<dash_id>', headers={'x-api-key':KEY})
dash = json.load(urllib.request.urlopen(req, timeout=30))

# 顶部 parameters（每个 slug 一个 entry，含 values_source_config + default + required）
new_params = [
  {'slug':'shop_name','name':'店铺','type':'category','sectionId':'string',
   'values_query_type':'list','values_source_type':'card',
   'values_source_config':{'card_id':lookup_ids['店铺名 (下拉)'][0],
       'value_field':['field','店铺',{'base-type':'type/Text'}]},
   'default':'香港主体店铺(北美)','required':True,'id':str(uuid.uuid4())},
  {'slug':'marketplace_name','name':'市场','type':'category','sectionId':'string',
   'values_query_type':'list','values_source_type':'card',
   'values_source_config':{'card_id':lookup_ids['市场名 (下拉)'][0],
       'value_field':['field','市场',{'base-type':'type/Text'}]},
   'default':'美国','required':True,'id':str(uuid.uuid4())},
  {'slug':'parent_asin','name':'Parent ASIN','type':'category','sectionId':'string',
   'values_query_type':'search','values_source_type':'card',
   'values_source_config':{'card_id':lookup_ids['parent_asin (搜索)'][0],
       'value_field':['field','parent_asin',{'base-type':'type/Text'}]},
   'id':str(uuid.uuid4())},
  # ... 其余维度类似
  {'slug':'start_date','name':'开始日期','type':'date/all-options','sectionId':'date','id':str(uuid.uuid4())},
  {'slug':'end_date','name':'结束日期','type':'date/all-options','sectionId':'date','id':str(uuid.uuid4())},
  {'slug':'granularity','name':'时间粒度','type':'category','sectionId':'string','default':'week','id':str(uuid.uuid4())},
]
dash['parameters'] = new_params
param_by_slug = {p['slug']: p['id'] for p in new_params}

# 每个 dashcard 的 parameter_mappings 重新生成
keep_dcs = []
for dc in dash['dashcards']:
  card_slugs = <这张卡的 SQL 用到的 template-tag 列表>  # 从 card.template-tags keys 拿
  mappings = [
    {'parameter_id': param_by_slug[slug], 'card_id': dc['card_id'],
     'target': ['variable', ['template-tag', slug]]}
    for slug in card_slugs if slug in param_by_slug
  ]
  keep_dcs.append({
    'id': dc['id'], 'card_id': dc['card_id'],
    'dashboard_tab_id': dc.get('dashboard_tab_id'),
    'row': dc['row'], 'col': dc['col'], 'size_x': dc['size_x'], 'size_y': dc['size_y'],
    'parameter_mappings': mappings,
    'visualization_settings': dc.get('visualization_settings') or {},
    'series': [s.get('id') if isinstance(s,dict) else s for s in (dc.get('series') or [])],
    'action_id': dc.get('action_id'),
    'inline_parameters': dc.get('inline_parameters') or [],
  })

payload = {'dashcards': keep_dcs, 'tabs': [{'id':t['id'],'name':t['name'],'position':t['position']} for t in dash['tabs']], 'parameters': new_params}
urllib.request.urlopen(urllib.request.Request(f'{API}/api/dashboard/<dash_id>',
  data=json.dumps(payload).encode(), method='PUT',
  headers={'x-api-key':KEY,'Content-Type':'application/json'}), timeout=60)
```

---

## 关键陷阱（一定踩过）

### ⚠️ Question 直链不应用 default

**症状**：用户从 dashboard 跳到 question 详情（如 `/question/1666-...`）时，shop_name 没生效，看到全市场数据。

**根因**：Metabase question 直链时，如果 template-tag 没有 `required: true`，且 URL 没传该参数，`[[ AND ... ]]` 占位符会被**整段跳过**，不应用 default。

**修复**：把所有"必须有的"筛选项设 `required: true` + `default`。

### ⚠️ values_source_config.value_field 列名必须 ASCII 安全或转义

如果 lookup card 的列名是中文（`店铺`/`市场`），写在 `value_field` 数组里没问题，但**列名要和 lookup card 实际输出的列名 100% 一致**（包括大小写和空格）。

实测可用：
```python
'value_field': ['field', '店铺', {'base-type': 'type/Text'}]
```

如果用别名，需用 `SELECT col AS "别名"` 引号包起来确保保留。

### ⚠️ template-tag 改了之后必须重新 wire dashcard

如果给一张已经在 dashboard 上的 card 新增 template-tag（比如加 shop_name），仅更新 card 不会自动 wire 到 dashboard 顶部参数——必须再 PUT dashboard 把 `parameter_mappings` 加上。

### ⚠️ Tab 切换不影响 dashboard 参数

dashboard 顶部参数是全局的，所有 tab 共享。如果某 tab 的卡没 wire 到顶部 shop_name，那 tab 就不响应。**必须每张卡都 wire**。

### ⚠️ values_query_type 不是 list/search 时

漏写或写错 `values_query_type` 默认会变成"none"（纯文本输入），UI 直接退化成文本框。**list 必须配 values_source_config**，否则下拉是空的。

### ⚠️ Dashboard PUT 时必须带完整 dashcards + tabs

即使只改 parameters，PUT `/api/dashboard/:id` 时 dashcards 漏掉就全清掉。**永远 GET 完整结构 → 改字段 → PUT 完整 payload**。

---

## 检查清单

新加一组筛选项后，过一遍：

- [ ] 每张目标 card 的 SQL 含 `[[ AND ... = {{tag}} ]]` 占位符
- [ ] 每张 card 的 `template-tags` 配置完整（id/name/type/required/default）
- [ ] 必填的 filter 设 `required: true` + `default`
- [ ] lookup card 已建好且 SQL 跑通（`SELECT col FROM ... ORDER BY ... LIMIT N`）
- [ ] dashboard 顶部 parameter 设了 `values_source_type='card'` + `values_source_config.card_id`
- [ ] 数量少（≤20）用 `values_query_type='list'`，大用 `'search'`
- [ ] 每张 dashcard 的 `parameter_mappings` 包含所有相关 template-tag
- [ ] Question 直链测试：不传 URL 参数也能跑出 default 数据
- [ ] Dashboard 跨 tab 测试：切到其他 tab 改顶部参数，所有卡跟着筛
- [ ] 默认值合理（如 `shop_name='香港主体店铺(北美)'` + `marketplace_name='美国'`）

---

## 反模式

- ❌ 在 SQL 里写死 ID（`WHERE shop_id='ATVPDKIKX0DER'`）— 改起来痛
- ❌ template-tag 不设 required + default → question 直链不生效
- ❌ 让用户输入业务 ID（如 `A1USBBMU2XLXD5`）— 改用中文名 + lookup
- ❌ 把所有维度都做下拉（5000 个 parent_asin 用 list 会卡死）— 大维度用 search
- ❌ 加 dashboard parameter 不 wire dashcard → 筛选没反应
- ❌ 单 card 改完不验证 question 直链是否生效