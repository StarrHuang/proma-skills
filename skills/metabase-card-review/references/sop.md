# Metabase Card Review SOP — 命令模板

## 1. 拉看板 + Card SQL

```python
import json, urllib.request
API = 'https://metabase.<your-host>'
KEY = '<your-api-key>'  # 从 env METABASE_API_KEY 或 mcp 配置

# 拉看板
req = urllib.request.Request(f'{API}/api/dashboard/<DASH_ID>',
                              headers={'x-api-key': KEY})
dash = json.load(urllib.request.urlopen(req, timeout=30))

# 每张 card 的 SQL
for dc in dash['dashcards']:
    cid = dc.get('card_id')
    if not cid: continue
    req = urllib.request.Request(f'{API}/api/card/{cid}', headers={'x-api-key': KEY})
    c = json.load(urllib.request.urlopen(req, timeout=30))
    with open(f'/tmp/dash_review/card_{cid}.sql', 'w') as f:
        f.write(f"-- {c['name']}\n")
        f.write(c['dataset_query']['native']['query'])
```

也可以直接走 Metabase MCP：
- `mcp__metabase__metabase_dashboard(dashboard_id=N)` 拿结构
- 没有直接拿 SQL 的工具，必须走 REST `/api/card/:id`

## 2. 提交 Card SQL（保留可视化配置）

```python
def update_card(cid, new_sql, vis_overrides=None, name=None, description=None):
    # GET 当前完整 payload
    req = urllib.request.Request(f'{API}/api/card/{cid}', headers={'x-api-key': KEY})
    d = json.load(urllib.request.urlopen(req, timeout=30))

    # 改 SQL
    d['dataset_query']['native']['query'] = new_sql

    # 合并可视化设置 (可选)
    vs = d.get('visualization_settings') or {}
    if vis_overrides:
        vs.update(vis_overrides)

    payload = {
        'dataset_query': d['dataset_query'],
        'display': d['display'],
        'visualization_settings': vs,
        'name': name or d['name'],
        'description': description or d.get('description'),
        'parameters': d.get('parameters') or [],
    }
    pr = urllib.request.Request(f'{API}/api/card/{cid}',
        data=json.dumps(payload).encode(), method='PUT',
        headers={'x-api-key': KEY, 'Content-Type': 'application/json'})
    return urllib.request.urlopen(pr, timeout=30).status
```

## 3. 冒烟测

```python
def smoke(cid):
    req = urllib.request.Request(f'{API}/api/card/{cid}/query',
        data=b'{}', method='POST',
        headers={'x-api-key': KEY, 'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return r.get('status'), r.get('row_count'), (r.get('error') or '')[:200]
```

必须 status='completed' 才算通过。

## 4. 看板 dashcard 调整（增删卡 / 重排位置）

PUT `/api/dashboard/:id` 要发完整 `{dashcards: [...], tabs: [...]}`。dashcard 字段必备：
- `id` (新建用负数), `card_id`, `dashboard_tab_id`（v50+ 有 tab 时必填）
- `row`, `col`, `size_x`, `size_y`
- `parameter_mappings`, `visualization_settings`, `series`, `action_id`, `inline_parameters`

完整示例见父 skill。

## 5. DDL 通道（建表/建 view）

Metabase 的 `/api/dataset` 支持多语句 DDL：

```python
sql = "SELECT 'start' AS marker; CREATE VIEW ...; CREATE TABLE ...; SELECT 'done' AS marker;"
payload = {"database": <DB_ID>, "type": "native", "native": {"query": sql}}
# DDL 静默执行, 仅返回首句 SELECT 结果, 验证用 information_schema 查表是否存在
```

前提：Metabase 配置的库账号有 CREATE 权限（验证：`SELECT has_schema_privilege('<schema>','CREATE')`）。

## 6. 备份原 SQL

每次改 SQL 前：
```bash
mkdir -p <cwd>/.context/sql_backup_<YYYYMMDD>
cp /tmp/dash_review/card_*.sql <cwd>/.context/sql_backup_<YYYYMMDD>/
```

## 7. 字段语义验证模板（每次必跑）

```sql
-- A. 字段注释
SELECT column_name, data_type,
       col_description((table_schema||'.'||table_name)::regclass, ordinal_position) AS comment
FROM information_schema.columns
WHERE table_schema='<schema>' AND table_name='<table>'
ORDER BY ordinal_position;

-- B. 关键字段分布
SELECT <group_field>, COUNT(*), SUM(<value>), AVG(<value>)
FROM <table>
WHERE <recent_date_filter>
GROUP BY 1
ORDER BY 2 DESC LIMIT 20;

-- C. 数学关系验证 (例: total = a + b + c?)
SELECT
  SUM(total) AS sum_total,
  SUM(a + b + c) AS sum_parts,
  SUM(total) - SUM(a + b + c) AS gap,
  COUNT(*) FILTER (WHERE total < a + b + c) AS bad_rows
FROM <table>;

-- D. 多对一验证
SELECT COUNT(*) total, COUNT(DISTINCT child) uniq_child,
       COUNT(DISTINCT (parent, child)) pairs
FROM <relation>;
```
