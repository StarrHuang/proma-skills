---
name: sales-forecasting
description: 销售预测与需求预测。构建统计/ML/DL/混合预测模型，特征工程，模型评估与选型，生产化部署。当用户需要预测销量、预测需求、时间序列预测、趋势预测、库存预测、季节性分析、做预测模型时触发。关键词：预测、forecast、prophet、ARIMA、XGBoost预测、需求计划、demand planning、时间序列。
---

# Sales Forecasting — 销售预测引擎

预测的目标不是猜数字，是**在物理约束下给决策者一个可行动的预判**。预测本身不优化现实，只描述"如果条件不变会发生什么"。

---

## 预测五大支柱（方法论核心）

### 支柱 1：最细粒度建模 → 自底向上聚合

**永远从最细粒度开始预测，再向上聚合。不要直接预测聚合量。**

原因：聚合量掩盖了组分的异质性。一个 parent ASIN 下不同 SKC 的生命周期、库存约束、增长率可以完全不同。

```
✗ 直接预测 parent ASIN 日销量 → 掩盖了 Beige 和 Brown 天壤之别
✓ 先预测每个 SKC → 聚合为 parent ASIN → 每条线都是可追溯的
```

**取数粒度层级**（由上到下，预测时反过来）：
```
Parent ASIN (B0CWK2YJTR)
  └─ SKC (CD20230103230970DJ-Beige, Grey, Green...)
       └─ SKU (CD20230103230970DJ-Beige-S, M, L, XL)
```

**规则**：
- SKC 是预测主粒度 — 不同颜色有独立需求曲线和库存约束
- SKU（尺码）按 SKC 内占比分配 — 一般不单独建模，除非尺码间需求差异极大
- 如果 SKC 内数据稀疏（新品、颜色多但每色销量低），可合并同类 SKC

**从 B0CWK2YJTR 案例学到的教训**：Beige 色 55.7% 需求只有 2.3 天库存，其他颜色撑一个月。聚合预测不会告诉你"马上要断的是哪个颜色"。

---

### 支柱 2：生命周期/增长状态分段建模

**不能用同一个模型预测所有阶段。必须先分类，再选模型。**

#### 生命周期阶段识别

| 阶段 | 特征 | 日销模式 | 适用预测模型 | 关键驱动因子 |
|------|------|---------|-------------|-------------|
| **测试期** | < 30天历史，波动大，无稳定模式 | 0→几十 | 定性判断 + 同类品类比 | 初始评分、价格、图片 |
| **爬坡期** | 稳定增长，WoW +10-30% | 几十→几百 | 指数平滑 + 趋势外推 | 排名爬升、评论积累 |
| **阶跃突破** | 某一周销量跳变 >50% WoW，BSR骤降 | 几百→上千 | **动量外推 + 硬约束上限** | 排名跃迁、病毒传播 |
| **稳态/成熟** | 波动在 ±20% 内，有季节规律 | 稳定 | ARIMA / Prophet / XGBoost | 季节性、促销、竞争 |
| **衰退期** | 持续下降，WoW -5-20% | 几百→几十 | 指数衰减拟合 | 竞品替代、评分下降、断货后恢复失败 |

#### 如何判断当前处于哪个阶段

```python
def classify_lifecycle(daily_sales: pd.Series) -> str:
    if len(daily_sales) < 30:
        return 'test'
    
    recent_14d = daily_sales[-14:].mean()
    prior_14d = daily_sales[-28:-14].mean()
    prior_28d_to_56d = daily_sales[-56:-28].mean()
    
    wow_growth = (recent_14d / prior_14d - 1) if prior_14d > 0 else float('inf')
    mom_growth = (recent_14d / prior_28d_to_56d - 1) if prior_28d_to_56d > 0 else float('inf')
    
    # 阶跃突破：WoW >50% 或 近7天均值 > 此前任一周均值的2倍
    last_7d = daily_sales[-7:].mean()
    max_prior_week = max(daily_sales[-56:-7].rolling(7).mean().dropna())
    if wow_growth > 0.5 or (max_prior_week > 0 and last_7d / max_prior_week > 2.0):
        return 'step_change'
    
    # 爬坡期
    if wow_growth > 0.1 and mom_growth > 0.2:
        return 'ramp_up'
    
    # 衰退期
    if wow_growth < -0.1 and mom_growth < -0.1:
        return 'decline'
    
    # 稳态
    return 'steady'
```

#### 阶跃突破期的特殊处理（最重要）

阶跃突破是预测最容易出错的情形。核心原因：**阶跃增长不是由历史趋势驱动的，而是由排名机制/社交传播驱动的非线性跃迁**。

**预测原则**：
1. **不能用 ARIMA/Prophet** — 它们会把过去 12 个月的"均值回归"趋势延伸到未来，严重低估
2. **不能用 YoY 做锚** — 去年同期的销量量和现在是两个世界
3. **用近期动量外推** — 最近 3-7 天的日均 × 适度增长因子
4. **增长不会永远持续** — 必须估算天花板

**天花板估算**（优先级从高到低）：
1. **库存硬顶** — FBA 可售 ÷ 日均 = 物理极限天数（最硬的约束）
2. **BSR/类目容量** — 该类目 Top 10 的平均日销是多少？你不可能超过第一名
3. **价格带容量** — 这个价格区间的总搜索量 × 合理 CVR = 理论上限
4. **历史峰值** — 同品类类似 ASIN 在巅峰期的日销

---

### 支柱 3：硬约束建模 — 预测 ≠ 愿望

**不把硬约束加进去的预测不是预测，是想象。** 物理约束决定了实际销量的上限。

#### 硬约束清单（按硬度排序）

| 约束 | 硬度 | 如何影响预测 | 建模方式 |
|------|------|-------------|---------|
| **FBA 可售库存** | 不可逾越 | 销量 ≤ 库存（当天） | SKC 级库存追踪 |
| **FBA 在途到货节奏** | 高（依ETA） | 何时恢复供应 | 时间窗口到货模拟 |
| **退货回收** | 中（延迟1-3周） | 销量 → 延迟回流 FBA 可售 | 退货率 × 可售率 × 延迟建模 |
| **BSR 排名** | 高 | BSR × 类目系数 ≈ 日销上限 | BSR→日销映射 |
| **BuyBox 占有率** | 中高 | BB% × 需求 = 可获得销量 | 折扣瓶颈 |
| **评分/评论数** | 中 | 低于 4.0 星 CVR 显著下降 | 评分衰减因子 |
| **广告预算/排名** | 中 | 广告停了流量减 X% | 广告占比关联 |
| **类目总搜索量** | 中 | 类目天花板 = 搜索量 × CVR | 类目容量上限 |
| **价格竞争力** | 中低 | 价格高于竞品 20% → CVR 降 | 价格弹性系数 |
| **季节性** | 中低 | 6 月牛仔可能回调 | 月级季节因子 |

#### 库存约束预测算法

```python
def constrained_forecast(daily_demand: list, skc_stocks: dict, 
                         arrivals: dict, horizon: int) -> pd.DataFrame:
    results = []
    stocks = skc_stocks.copy()
    
    for day in range(horizon):
        for skc, arrival_schedule in arrivals.items():
            if day in arrival_schedule:
                stocks[skc] = stocks.get(skc, 0) + arrival_schedule[day]
        
        day_sales = {}
        day_lost = {}
        for skc, demand in daily_demand[day].items():
            available = stocks.get(skc, 0)
            sold = min(demand, available)
            day_sales[skc] = sold
            day_lost[skc] = demand - sold
            stocks[skc] = available - sold
        
        results.append({
            'day': day,
            'total_demand': sum(daily_demand[day].values()),
            'total_sales': sum(day_sales.values()),
            'total_lost': sum(day_lost.values()),
            'ending_stock': sum(stocks.values()),
            'lost_detail': day_lost,
        })
    
    return pd.DataFrame(results)
```

#### 退货回收库存（关键 — 延长断货时间线）

**卖出去的货有一部分会回来。这个回收流能显著推迟断货。**

退货周期模型：
```
销售日 T: 卖出 N 件
T + 1~2周: 消费者退货 → Amazon 仓库接收
T + 2~3周: 质检 + 重新上架为 FBA 可售
→ T + ~2周后, 约 退货率 × 可售率 的库存回流
```

**核心参数**（需按 ASIN 历史数据估算，无数据时用类目基准）：

| 参数 | 时尚/服装典型值 | 如何获取 |
|------|---------------|---------|
| **退货率** | B0CWK2YJTR 实测 31.5%（25-38% 范围）| amazon_profit_statement.return_count / sale_count |
| **可售率** | 80-90% | 无直接数据，用 85% 基准 |
| **退货延迟** | 7-14 天（快）/ 14-21 天（慢） | 实测顾客寄回到 Amazon 处理 |
| **净回收率** | 退货率 × 可售率 ≈ 27% | — |
| **Amazon 预估** | expected_return_rate ≈ 0.1-0.2 | **严重低估，不可用** — 实测值 3x 于预估 |

**退货率数据获取规则（关键）**：

```sql
-- 正确：取 30-90 天前的数据，跳过近 4 周（退货窗口未关闭）
SELECT
    ROUND(SUM(return_count)::numeric / NULLIF(SUM(sale_count), 0) * 100, 1) AS return_pct
FROM plutus.amazon_profit_statement ps
JOIN oms_backup.amazon_catalog_item_relationship cir ...
WHERE cir.parent_asin = '{asin}'
  AND ps.statement_date BETWEEN CURRENT_DATE - 90 AND CURRENT_DATE - 28;
-- 不要包含近 28 天的数据 — 退货窗口未关闭, 数据不完整

-- 错误：直接用近一个月数据 → 退货率看起来是 5%, 实际是 32%
```

**为什么 Amazon 的 expected_return_rate 不可用**：实测 B0CWK2YJTR 真实退货率 31.5%，但 `expected_return_rate` 只显示 0.1-0.2（10-20%）。这个字段是 Amazon 的类目级预估值，不是 ASIN 级实测值，对时尚品类系统性低估。

**退货回收对 B0CWK2YJTR 的实际影响**（用实测 31.5%）：

```
假设: 退货率 30%, 可售率 85%, 回收延迟 10 天, 退货按 SKC 销量比例分配

May 18-24 周销量 2,149 → 回收 2,149 × 0.30 × 0.85 ≈ 550 件
  → 约 Jun 1-7 回到 FBA 可售
  → Beige (55.7%): ~306 件 → 多撑 ~0.9 天
  → Grey (20.3%): ~112 件 → 多撑 ~0.8 天

May 25-31 预计销量 (断货前): ~1,800 件 → 回收 ~460 件
  → 约 Jun 8-14 回到 FBA
  → 在 W2-W3 关键窗口提供缓冲
```

**效果总结**：30% 退货率在高峰期相当于每 3 周自动补充约一周的销量。但它是**延迟回流**，不能替代 FBA 在途到货——只能让断货推迟 1-2 天，不能消除结构性的库存缺口。

**集成到约束预测**：

```python
def return_recycling(sales_history: list, return_rate: float,
                    relist_rate: float, delay_days: int,
                    skc_shares: dict) -> dict:
    """
    skc_shares: {skc: share_pct}  各SKC销量占比
    Returns: {skc: {day: qty}}  每个SKC每天的回流入库量
    """
    net_return_rate = return_rate * relist_rate
    recycling = {skc: {} for skc in skc_shares}
    
    for i, sales in enumerate(sales_history):
        day_of_return = delay_days - i  # 正数 = 在未来
        if day_of_return > 0:
            total_return = sales * net_return_rate
            for skc, share in skc_shares.items():
                qty = total_return * share
                recycling[skc][day_of_return] = recycling[skc].get(day_of_return, 0) + qty
    
    return recycling

# 集成方式: 在 constrained_forecast() 每天循环中:
# for day in range(horizon):
#     # 1. FBA 在途到货
#     stocks[skc] += arrivals.get(skc, {}).get(day, 0)
#     # 2. 退货回收入库
#     stocks[skc] += return_schedule.get(skc, {}).get(day, 0)
#     # 3. 扣除当日销量
#     ...
```

**数据获取**（如果 performance_statement.refund_count 为空）：

```sql
-- 备选方案: 从 profit_statement 或 OMS 获取退货率
-- 如果 DB 不可用, 用类目基准:
--   女装: 25-35% | 男装: 15-25% | 鞋: 20-30%
--   电子产品: 5-15% | 家居: 5-10% | 玩具: 10-20%
```

---

### 支柱 4：MECE 分解 → 独立建模 → 聚合

**把预测问题 MECE 拆成互斥的子问题，各自独立建模，再组合。**

#### MECE 分解框架

```
销售预测
├── 需求端（不受限）
│   ├── 趋势分量（长期增长/衰减方向）
│   ├── 周内季节分量（周一~周日模式）
│   ├── 月级季节分量（1~12月周期性）
│   ├── 假日效应（固定假日 + 浮动假日）        ← 独立分支，不用 YoY 隐含
│   ├── 大促事件（Prime Day / BFCM / 会员日）   ← 独立处理，非线性
│   ├── 价格弹性分量（折扣 → 需求变化）
│   └── 外部冲击分量（排名跃迁、病毒传播、竞品动作）
│
├── 供给端（约束）
│   ├── FBA 库存级联（可售 → 预留 → 在途 7d/8-21d/22d+）
│   ├── 采购在途（PW 未交付 → 质检 → 入库 → 调拨 → FBA 签收）
│   ├── 退货回收（销量 × 退货率 × 可售率 → 延迟回流 FBA）  ← 自循环补充
│   └── 产能上限（工厂产能、物流瓶颈）
│
├── 竞争端（市场容量）
│   ├── BSR 位次 → 日销映射
│   ├── 价格带搜索量
│   └── 竞品数量 × 评分
│
└── 运营端（可控变量）
    ├── 广告投放（预算、竞价、ACoS）
    ├── 促销计划（LD、coupon、会员折扣）
    └── Listing 优化（主图、A+、关键词）
```

#### 假日与 YoY 的 MECE 关系（关键）

**核心问题**：如果已经在最细粒度做预测，假日效应是不是自然被 YoY 包含了？答：**部分包含，但不能依赖。必须显式建模。**

| 假日类型 | YoY 能捕获？ | 建模方式 | 原因 |
|---------|-------------|---------|------|
| **固定日期假日** (Christmas 12/25, New Year 1/1, July 4) | 能 — 有 ≥2 年 SKC 级历史 | 直接取 乘法因子 | 每年同一天 |
| **固定星期假日** (Thanksgiving 11月第4周四, Memorial Day 5月最后周一) | 部分能 — 日期偏移 1-6 天 | YoY + 日期对齐 | 需要先对齐到同一星期 |
| **浮动假日** (Easter 3/22-4/25 之间) | 不能 | 显式日期特征 | 日期范围跨度大 |
| **Amazon 特定事件** (Prime Day, BFCM) | 不能 | 独立事件模型 | 日期变动 + 非线性效应 + 促销机制驱动 |
| **中国假日影响** (春节工厂停工) | 不能 | 采购/产能端显式建模 | 影响供给侧, 不是需求侧 |
| **阶跃期 SKC 的假日** | YoY 失效 | 用"近期基线 × 假日乘数" | 去年的销量量不相关 |

**MECE 处理规则**：

```
For each SKC:
  if has_2y_history AND stage in ('steady', 'decline'):
    假日效应 = SKC级YoY假日周/非假日周 比值  ← YoY 涵盖
    + 显式修正: 浮动假日、日期偏移 >3天的假日
  
  elif stage in ('test', 'ramp_up', 'step_change'):
    假日效应 = 同类目同阶段SKC的假日乘数中位数  ← 跨SKC借用, 不用YoY
    + 按该SKC近30天基线缩放
  
  For ALL SKCs:
    Prime Day / BFCM → 独立事件模型（见下方"大促事件建模"）
    春节供应影响 → 在供给端 PW/产能 建模（不是需求端）
```

**为什么不能用"聚合层 YoY"替代**：
聚合层（parent ASIN）的 YoY 假日因子会混淆结构变化。一个 ASIN 去年 7/4 卖了 30 件、今年卖 300 件 — 假日乘数看起来是 10x，但实际上是生命周期驱动，不是假日驱动。必须先在 SKC 级去趋势，再提取假日因子。

#### 大促事件建模（Prime Day / BFCM）

大促不能当"假日"处理 — 这是完全不同的需求生成机制。

```
Prime Day 效应模型:
├── 预热期 (T-7 ~ T-1)
│   └── 日销 = 基线 × (0.75 ~ 0.85)   ← 消费者等待Deal
├── 大促日 (T ~ T+1, 通常2天)
│   ├── Deal ASIN: 基线 × (2.0 ~ 5.0)  取决于折扣深度和Deal类型
│   ├── 非Deal ASIN: 基线 × (1.2 ~ 1.5)  光环效应
│   └── 上限 = FBA可售库存  ← 物理极限
├── 余热期 (T+2 ~ T+7)
│   └── 日销 = 基线 × (0.6 ~ 0.8)   ← 透支了未来需求
└── 恢复期 (T+8 ~ T+21)
    └── 日销 → 基线 × (0.9 → 1.0) 线性恢复
```

**Prime Day 预测工作流**：

```python
def prime_day_forecast(baseline_daily: float, deal_type: str, 
                       discount_pct: float, fba_stock: int) -> dict:
    multipliers = {
        'Lightning_Deal': (2.0, 4.0),
        'Best_Deal': (2.5, 5.0),
        'Prime_Exclusive_Discount': (1.5, 2.5),
        'Coupon_Only': (1.2, 1.8),
        'No_Deal': (1.0, 1.3),  # 光环效应
    }
    base_mult, max_mult = multipliers.get(deal_type, (1.2, 1.5))
    discount_mult = 1 + (discount_pct - 20) / 100  # 20% 折扣为基准
    event_mult = min(base_mult * discount_mult, max_mult)
    max_daily_from_stock = fba_stock / 2  # 2天大促, 不能第一天卖光
    
    return {
        'pre_event_daily': baseline_daily * 0.8,
        'event_daily': min(baseline_daily * event_mult, max_daily_from_stock),
        'post_event_daily': baseline_daily * 0.7,
        'recovery_weeks': 3,
    }
```

**BFCM (Black Friday / Cyber Monday)**：
- 效应比 Prime Day 略弱但持续更久（整个 Thanksgiving 周末 + Cyber Week）
- 预热期更长（消费者从 11 月初开始推迟购买）
- 需要同时考虑竞争加剧（所有卖家都在促销，价格战更激烈）

#### 各分支的建模方法

| 分支 | 模型 | 数据需求 | 输出 |
|------|------|---------|------|
| **趋势分量** | 近 14d 均值 × 衰减因子 | 日销序列 | 未来 30d 日均基线 |
| **周内季节** | 周内 7 因子 × 基线 | ≥ 4 周历史 | 日级调整系数 |
| **月级季节** | 月级 12 因子 × 基线 | ≥ 2 年历史或类目借用 | 月级调整系数 |
| **假日效应** | SKC 级假日乘数(去趋势后) | 同 SKC 2 年或同类目借用 | 假日日级乘数 |
| **大促事件** | 独立事件模型(预热+峰值+余热) | 历史大促数据或类目基准 | 事件窗口日销 |
| **价格弹性** | log(需求) ~ log(价格) 回归 | 历史价格 + 销量 | 弹性系数 ε |
| **库存约束** | 逐日库存追踪模拟（含退货回收） | v_inventory_snapshot + FBA 在途 + 退货率 | 约束后日销 |
| **BSR 天花板** | BSR→日销 幂律拟合 | 同类 ASIN 的 BSR + 日销 | 日销上限 |
| **广告贡献** | 广告销量占比 × 预算弹性 | performance ads_* 字段 | 广告关停影响 |

---

### 支柱 5：阶跃触发预测与断货后恢复建模

**预测什么触发阶跃 + 阶跃撞墙后的状态 + 二次补货能否重新阶跃。**

#### 5.1 阶跃触发条件检测

阶跃不是随机事件。它由可观测的前置信号驱动。我们虽然不能精确预测"哪天阶跃"，但可以评估"阶跃发生的条件是否成熟"。

```
阶跃触发信号（按预测力排序）:
1. BSR 衰退加速度 — 连续 7d BSR 每天下降 ≥ 5 位 → 正向飞轮启动
2. Sessions 增长脱离 CVR — Sessions +50% 但 CVR 不变 → 算法在推流量
3. 评论数突破阈值 — 50+ / 100+ / 500+ 评论阶段 CVR 有跳跃
4. 竞品断货 — 类目 Top 10 中 ≥2 个 ASIN 库存耗尽 → 需求释放
5. 关键词排名跳升 — 核心词从第2页跃至第1页 → 流量质变
6. 社交媒体信号 — (需外部数据) TikTok/IG 提及量暴增
```

**阶跃概率评分**：

```python
def step_change_probability(skc_data: dict) -> float:
    score = 0.0
    
    # BSR 衰减加速度 (连续下降 → 正向)
    bsr_trend = skc_data['bsr_7d_trend']  # 负值 = BSR在改善
    if bsr_trend < -5:  # 每天降5+位
        score += 0.25
    elif bsr_trend < -2:
        score += 0.10
    
    # Sessions 脱离 CVR 增长
    session_growth = skc_data['sessions_7d'] / skc_data['sessions_14d_prior'] - 1
    cvr_change = skc_data['cvr_7d'] - skc_data['cvr_14d_prior']
    if session_growth > 0.3 and cvr_change > -0.1:  # 流量涨但CVR不降
        score += 0.20
    
    # 评论突破阈值
    reviews = skc_data['review_count']
    if reviews >= 100 and skc_data['reviews_30d_ago'] < 100:
        score += 0.15
    elif reviews >= 50 and skc_data['reviews_30d_ago'] < 50:
        score += 0.10
    
    # 竞品断货 (需类目数据)
    if skc_data.get('competitors_oos', 0) >= 2:
        score += 0.25
    elif skc_data.get('competitors_oos', 0) >= 1:
        score += 0.15
    
    # 关键词排名跳升
    if skc_data.get('kw_rank_jump', False):  # 核心词从 >20位 → <10位
        score += 0.15
    
    return min(score, 1.0)

# 解读:
# ≥0.6: 高概率近期阶跃, 应准备库存场景
# 0.4-0.6: 中等可能, 持续监控前置信号
# <0.4: 无明显阶跃信号
```

#### 5.2 阶跃撞墙预建模（Scenario Planning）

在阶跃概率较高时，预先计算"如果阶跃发生，系统会在哪里撞墙"：

```python
def step_change_wall(skc: str, current_daily: float, 
                     step_multipliers: list, skc_stocks: dict,
                     arrivals: dict, market_cap: float) -> dict:
    """
    模拟不同阶跃倍率下的撞墙时间和销量损失
    step_multipliers: [2x, 3x, 5x] 不同阶跃强度
    """
    scenarios = {}
    for mult in step_multipliers:
        demand = current_daily * mult
        stock = skc_stocks[skc]
        days_to_oos = stock / demand if demand > 0 else float('inf')
        
        # 如果库存够, 是否触及市场容量天花板
        hits_market_cap = demand > market_cap
        
        # 在途能否救急
        rescue_day = None
        for day, qty in sorted(arrivals.get(skc, {}).items()):
            if days_to_oos <= day:
                rescue_day = day
                break
        
        scenarios[f'{int(mult)}x'] = {
            'new_daily': round(demand),
            'days_to_oos': round(days_to_oos, 1),
            'oos_date': f'Day {round(days_to_oos, 1)}',
            'hits_market_cap': hits_market_cap,
            'first_arrival_rescue': rescue_day,
            'can_sustain': days_to_oos > rescue_day if rescue_day else days_to_oos > 7,
        }
    return scenarios

# B0CWK2YJTR Beige 示例:
# 当前日均 346, 库存 500 → 即使不继续加速, 1.4 天断
# 2x → 692/d → 0.72 天断 → 在途 8 天后才到 → 断 6+ 天
# 结论: Beige 在任何阶跃场景下都会断货, 且恢复窗口 >7 天
```

#### 5.3 断货后恢复建模（阶跃窗口期）

**核心问题**：断货后补货，还能重新阶跃吗？

这取决于三个关键变量：
1. **断货时长** — 越短恢复越快
2. **BSR 退化程度** — 断货期间 BSR 上升到什么位置
3. **竞品是否趁机占据** — 有没有替代品抢了需求

```
断货恢复模型:
├── 断货 ≤ 3 天 (轻微)
│   ├── BSR 上升 20-50%   ← 轻微惩罚
│   ├── 补货后 2-4 天恢复至断前 80-90% 水平
│   └── 结论: 仍在阶跃窗口内, 大概率重拾动能
│
├── 断货 4-7 天 (中等)
│   ├── BSR 上升 50-200%  ← 显著退化
│   ├── 竞品开始占据关键词排名
│   ├── 补货后 1-2 周恢复至断前 50-70% 水平
│   └── 结论: 阶跃窗口部分关闭, 需重新爬坡
│
├── 断货 8-14 天 (严重)
│   ├── BSR 上升 200-500%  ← 严重退化
│   ├── 竞品已稳定占据你的位置
│   ├── 补货后需 3-6 周爬回, 可能只能恢复至断前 30-50%
│   └── 结论: 阶跃窗口基本关闭, 重新爬坡
│
└── 断货 >14 天 (灾难)
    ├── BSR 回到断前位置或更差
    ├── 等于重新推新品
    └── 结论: 阶跃窗口完全关闭
```

**B0CWK2YJTR Beige 的恢复预判**：
- 断货开始：May 30-31
- 在途 8-21d 到货：Jun 6-7 开始 (Beige 280件)
- 断货时长：**~7 天** ← 恰好卡在"中等"区间
- 在途 22d+ 到货：Jun 19 开始 (Beige 1,604 件) ← 大量到货
- 预判：Jun 6 有 280 件 Beige 到仓 → 可恢复约 70% 断前水平 (280/346 = 0.8 天就卖完, 不够)
- 真正恢复需要等 Jun 19 的 1,604 件 → 断货 ~20 天 → **"严重"区间, 阶跃窗口关闭**
- 除非：PW 5,870 件提前交付, 或 LA 1,560 件加急调拨

**恢复预测模型**：

```python
def recovery_forecast(pre_oos_daily: float, oos_duration_days: int,
                      restock_qty: int, category_competitiveness: str) -> dict:
    """
    pre_oos_daily: 断货前日均
    oos_duration_days: 断货持续天数
    restock_qty: 补货量
    category_competitiveness: 'high'/'medium'/'low'
    """
    # 恢复比例 vs 断货时长 (经验参数, 需按类目校准)
    if oos_duration_days <= 3:
        recovery_pct = 0.85
        recovery_weeks = 1
    elif oos_duration_days <= 7:
        recovery_pct = 0.60
        recovery_weeks = 2
    elif oos_duration_days <= 14:
        recovery_pct = 0.35
        recovery_weeks = 4
    else:
        recovery_pct = 0.15
        recovery_weeks = 8
    
    # 竞争激烈度修正
    comp_discount = {'high': 0.8, 'medium': 0.9, 'low': 1.0}
    recovery_pct *= comp_discount.get(category_competitiveness, 1.0)
    
    # 补货量是否足够支撑恢复
    weekly_need = pre_oos_daily * recovery_pct * 7
    can_sustain = restock_qty >= weekly_need * recovery_weeks
    
    return {
        'recovery_pct': round(recovery_pct * 100),
        'recovery_daily': round(pre_oos_daily * recovery_pct),
        'recovery_weeks': recovery_weeks,
        'step_change_window_open': oos_duration_days <= 7,
        'can_sustain': can_sustain,
        'risk': 'restock_qty insufficient' if not can_sustain else None,
    }
```

---

## 完整预测工作流

### Phase 0: 生命周期分类 + 阶跃概率评估

```
1. 取 SKC 级日销历史 (≥ 90 天)
2. 每个 SKC 判生命周期阶段 (classify_lifecycle)
3. 对阶跃期/爬坡期 SKC, 额外评估:
   a. 阶跃触发概率 (step_change_probability)
   b. 阶跃撞墙场景 (step_change_wall) — 如果触发, 会撞在哪里
4. 排除死 SKC
```

### Phase 1: 不受限需求预测 (含假日/事件调整)

```python
def forecast_unconstrained(skc_daily: pd.Series, stage: str, 
                           holiday_calendar: pd.DataFrame,
                           prime_day_window: tuple = None) -> list:
    recent_7d_avg = skc_daily[-7:].mean()
    
    if stage == 'step_change':
        base = skc_daily[-3:].mean()
        trend = [base * (1 + 0.08 * max(0, 1 - d/30)) for d in range(60)]
    
    elif stage == 'ramp_up':
        growth_rate = (skc_daily[-14:].mean() / skc_daily[-28:-14].mean()) ** (1/14) - 1
        trend = [recent_7d_avg * (1 + growth_rate) ** d for d in range(60)]
    
    elif stage == 'steady':
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        model = ExponentialSmoothing(skc_daily, seasonal_periods=7, trend='add', seasonal='add')
        fitted = model.fit()
        trend = fitted.forecast(60).tolist()
    
    elif stage == 'decline':
        decay = (skc_daily[-14:].mean() / skc_daily[-28:-14].mean())
        trend = [recent_7d_avg * decay ** (d/7) for d in range(60)]
    
    else:  # test
        trend = [recent_7d_avg] * 60
    
    # === 假日调整 (不是乘以去年, 是去趋势后乘因子) ===
    holiday_mult = get_holiday_multiplier(skc_daily, stage, holiday_calendar)
    trend = [t * holiday_mult.get(d, 1.0) for d, t in enumerate(trend)]
    
    # === 大促事件覆盖 ===
    if prime_day_window:
        trend = apply_prime_day(trend, prime_day_window, deal_type, fba_stock)
    
    return trend
```

### Phase 2: SKC → Parent 聚合（不受限）

```python
parent_unconstrained = pd.DataFrame({
    skc: forecast_unconstrained(data[skc], stages[skc], holidays)
    for skc in active_skcs
}).sum(axis=1)
```

### Phase 3: 施加库存约束

取每个 SKC 的库存初始值 + 在途到货计划，逐日模拟：

```python
constrained = constrained_forecast(skc_daily_demand, skc_stocks, arrivals, horizon=60)
```

### Phase 4: 施加市场天花板 + 阶跃恢复衰减

```python
# 对于经历过断货的 SKC, 恢复后施加衰减因子
for skc in oos_skcs:
    recovery = recovery_forecast(pre_oos_daily, oos_days, restock_qty, competitiveness)
    constrained[skc] *= recovery['recovery_pct'] / 100  # 恢复期内打折

# BSR 天花板
constrained['sales'] = np.minimum(constrained['sales'], market_cap * dow_factor)
```

### Phase 5: 输出

1. **不受限需求轨迹** — 如果库存无限会卖多少
2. **库存约束轨迹** — 实际能卖多少
3. **阶跃窗口状态** — 哪些 SKC 在阶跃, 哪些在恢复
4. **断货恢复预判** — 补货后预计恢复到断前多少 %

---

## 模型评估（回测）

### 分阶段回测

```python
def backtest_by_stage(model, data, stage, n_windows=5):
    if stage in ('test', 'step_change'):
        windows = [(len(data) - 14, len(data) - 7)]
    elif stage == 'ramp_up':
        data = data[-90:]
        windows = [(i, i+7) for i in range(0, len(data)-14, 7)]
    else:
        windows = [(i, i+30) for i in range(0, len(data)-60, 30)]
    
    errors = []
    for train_end, test_end in windows:
        train, test = data[:train_end], data[train_end:test_end]
        preds = model.fit_predict(train, len(test))
        errors.append(mape(test, preds))
    
    return np.mean(errors), np.std(errors)
```

### 多维度评估

| 维度 | 为什么要看 | 方法 |
|------|-----------|------|
| 按 SKC 评估 | 避免好 SKC 掩盖差 SKC | 每个 SKC 单独算 WAPE |
| 按生命周期评估 | 阶跃期的误差和稳态不一样 | 分组报告 |
| 按预测 horizon | 7d 和 30d 是不同难度 | 分别报告 7d/14d/28d |
| 约束模型 vs 不受限 | 约束模型应更准（贴近现实） | 对比两者 MAPE |
| 大促窗口独立评估 | 大促事件不参与常规评估 | 只在事件窗口内评估 |

---

## 预测输出规范

### 输出模板

```
## {ASIN} 约束预测

### 当前状态
- 生命周期阶段: {stage}
- 阶跃概率评分: {X}/1.0 (触发信号: {哪些})
- 近 7d 日均: {X} 件 | WoW: {+X%} | 朴素基线(shift-7): {X} 件

### 不受限需求预测 (无限库存 + 假日调整)
| Horizon | 中位 | P10 | P90 | 关键假日/事件 |
|---------|------|-----|-----|-------------|
| 7d     |      |     |     |             |
| 14d    |      |     |     |             |
| 28d    |      |     |     |             |

### 库存约束预测 (实际条件)
| Horizon | 约束销量 | 丢失销量 | 丢失GMV | 主要瓶颈 |
|---------|---------|---------|---------|---------|
| 7d      |         |         |         | {SKC} Day{N}断 |
| 14d     |         |         |         |            |
| 28d     |         |         |         |            |

### 断货日历
{日期}: {SKC} 耗尽 → 日销从 {X} 降至 {Y}

### 阶跃触发预判
- 概率: {X}% | 信号: {BSR加速/流量暴增/竞品断货/...}
- 如果阶跃 {2x/3x/5x}: 撞墙日 = {date}, 瓶颈 = {库存/BSR上限}

### 断货恢复预判
- {SKC}: 预计断 {N} 天 → 恢复至 {X}% 断前水平 → {窗口开/关}
- 恢复需 {Q} 件补货, 当前在途 {R} 件 → {够/不够}

### 可信度
- 回测 MAPE: {X}% | 朴素基线: {Y}%
- 假日调整方法: {YoY / 跨SKC借用 / 显式特征}
- 最大不确定性: {什么假设如果错了影响最大}

### 关键假设
1. {假设1}
2. {假设2}
```

---

## 库选型

```python
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, HoltWinters, SeasonalNaive
import statsmodels.api as sm
import lightgbm as lgb
import xgboost as xgb
from sklearn.linear_model import QuantileRegressor
```

---

## 常见陷阱

| 陷阱 | 表现 | 纠正 |
|------|------|------|
| **直接预测聚合量** | 只看 parent ASIN, 忽略各颜色差异 | 预测粒度 = SKC → 聚合 |
| **阶跃期用 ARIMA** | 对历史均值回归, 严重低估爆发增长 | 改用动量外推 + 天花板 |
| **预测不考虑库存** | 预测六月卖 2 万件, 实际 FBA 只够 8 天 | 先跑库存约束再出数 |
| **YoY 作为假日唯一基准** | 阶跃期 YoY 不相关, 用 10x 假日因子 | SKC级去趋势后提取, 阶跃期借用同类 |
| **假日和大促混为一谈** | 用假日模型处理 Prime Day | 大促独立事件模型 |
| **忽略断货后的恢复衰减** | 假设补货后立刻恢复断前日销 | 断货时长 → 恢复比例建模 |
| **不做阶跃撞墙预建模** | 阶跃发生后才慌 | 阶跃信号出现时预跑场景 |
| **忽略生命周期切换** | 一个模型覆盖全生命周期 | 先分类, 再建模 |
| **不定期回测** | 模型失效了还在用 | 生命周期阶段变化时触发重评估 |
