---
name: troas-adjust
description: >
  运行 Google Ads Target ROAS (tROAS) 每日分析报告，展示待调整清单并可确认执行调整。
  适用于大预算女装 Shopping/PMax 账户的每日 tROAS 自动化运营。
  注意：此为 Google Ads 出价策略（Target ROAS），非金融 TROAS (Total Return on Asset Swap)。

  触发词: tROAS调整、广告出价调整、ROAS优化、troas report、调整出价、Google Ads出价。
allowed-tools: Bash
---

运行 tROAS 每日调整流程，步骤如下：

**第一步：运行 report 模式**

用 Bash 执行：
```
cd /Users/cider/Developer/mcp-google-ads && .venv/bin/python troas_daily_adjust.py --mode report
```
超时设置 180 秒（脚本会连接数据仓库，并调用 Google Ads API v21 拉取当前 tROAS）。

**第二步：展示报告**

将完整输出展示给用户（包括报告表格和待调整条数汇总）。`report` 模式会把待执行计划保存到 `/tmp/troas_pending.json`，供后续 `execute` 模式读取，同时自动将完整报告存档为 CSV 文件（`reports/troas_YYYY-MM-DD.csv`）。生成报告后，默认还需要通过飞书把报告发送给黄百兴，便于其先行查看待调整清单。

**第三步：询问确认**

报告展示完毕后，问用户：

> 以上报告已生成，待调整计划已保存。**是否现在执行 tROAS 调整？**
> - 回复「执行」→ 立即运行 execute 模式
> - 回复「取消」或不回复 → 不执行（可稍后手动运行）

**第四步：按用户回复执行**

若用户确认执行，运行：
```
cd /Users/cider/Developer/mcp-google-ads && .venv/bin/python troas_daily_adjust.py --mode execute
```
超时 120 秒，展示执行结果（成功/失败明细）。`execute` 模式会读取 `/tmp/troas_pending.json`，执行后删除该文件，并发送飞书 webhook + 本机通知。

---

## 调整规则参考

| 条件 | 操作 |
|------|------|
| 含 `brandterm` | 不修改 |
| AI托管（见下方名单） | 仅评价 |
| 7天花费 < $100 | tROAS -10%（固定） |
| 加权eROI 在目标 ±5% 以内 | 无需调整（死区） |
| 加权eROI < 1.25 | tROAS +(缺口/加权)×1.5×系数，季节修正，+25% 上限 |
| 加权eROI > 1.25 | tROAS -(超额/加权)×1.5×系数，季节修正，-25% 下限 |

**加权 eROI** = 昨日×65% + 7日×35%（昨日 eROI > 0 时使用双权重；否则仅用 7 日）

**死区逻辑**：当 blended eROI 落在 `1.25 ± 5%` 区间内（即 1.1875 ~ 1.3125）时，输出 `无需调整`，不生成新的 tROAS。

## 调整方向说明

- **加权 eROI 低于目标**：提高 tROAS，收紧出价，优先修复 ROI。
- **加权 eROI 高于目标**：降低 tROAS，放宽出价，争取更多流量与花费。
- 对大预算账户而言，这不是“高 ROI 就不动”，而是“高于目标时适度放量”，避免因 tROAS 过紧而错失增量。

## 季节性修正细则

| 去年同期未来 2 周趋势 | 加权eROI < 1.25（上调 tROAS） | 加权eROI > 1.25（下调 tROAS） |
|---|---|---|
| 下期改善 > +10% | ×0.75（温和上调） | ×1.2（积极放量） |
| 下期恶化 < -10% | ×1.2（积极收紧） | ×0.75（保守放量） |
| 其他 | ×1.0 | ×1.0 |

## 调用方式与调整系数

| 调用方式 | 系数 | 说明 |
|---|---|---|
| `--mode report` | ×1.0（默认） | 手动分析，待人工确认 |
| `--mode execute` | 继承 report 时已保存的计划 | 从 `/tmp/troas_pending.json` 读取并执行 |
| `--mode auto --multiplier 1.0` | ×1.0 | 分析 + 立即执行，无确认 |
| `--mode auto --multiplier 0.7` | ×0.7 | 适合外部定时任务做保守执行 |

如需 13:00 等固定时间自动执行，需要由外部 cron / launchd 调用 `--mode auto --multiplier 0.7`；脚本本身不带调度器。

## AI托管不修改的 campaign

- pla-au-label0-w2plpcs-daba-au-230617
- pla-de-label0-w2plpcs-daba-de-230922
- pla-fr-allprod-w2plpcs-daba-fr-ios-231010
- pla-gb-allprod-w2plpcs-daba-gb-230527
- pla-gb-allprod-w2plpcs-daba-gb-ios-231010
- pla-nl-allprod-w2plpcs-daba-nl-ios-230922
- pla-us-label0-w2plpcs-daba-us-230730

## 通知渠道

| 时机 | 飞书（Webhook POST，发送给黄百兴） | 本机推送（osascript） |
|------|-----------------------------------|----------------------|
| `report` 生成后 | 待调整清单 + "待确认执行" | ✓ |
| `execute` 完成后 | 执行结果（成功/失败明细） | ✓ |
| `auto` 完成后 | 执行结果（成功/失败明细） | ✓ |

飞书通过 `FEISHU_WEBHOOK_URL` 环境变量配置；未设置时会回落到脚本中的默认 webhook。默认要求报告和执行结果通过飞书发送给黄百兴。无需 `lark-cli`。

## 大预算女装运营注意事项

- 单次调整幅度虽然封顶 ±25%，但这正是大预算账户的安全阀。对于连续多日偏离目标的 campaign，应让系统按日逐步收敛，而不是手动一次性大改。
- 女装账户受周内波动、闪促、上新、内容热点影响较大。大促窗口、重大活动日、强素材上新期，可在自动执行前先人工复核，避免短期异常被误判为长期信号。
- 该脚本只会真正修改 **已有 tROAS 值** 的 campaign。缺少 `target_roas` 的 campaign 会出现在报告中，但属于 `缺tROAS跳过`，需先完成出价策略迁移。
- AI托管 campaign 保留在报告中仅用于评价，不纳入自动改价。若要移出名单，先和对应托管策略负责人确认。

## 脚本

`/Users/cider/Developer/mcp-google-ads/troas_daily_adjust.py`

参数调整（脚本顶部常量）：
- `TARGET_EROI` 目标 eROI（默认 1.25）
- `WEIGHT_YD / WEIGHT_7D` 权重（默认 0.65 / 0.35）
- `ADJ_BASE` 基准系数（默认 1.5）
- `LOW_SPEND_THR` 低花费阈值（默认 $100）
- `PENDING_FILE` 待执行计划文件（默认 `/tmp/troas_pending.json`）
- `REPORTS_DIR` CSV 存档目录（默认 `<script_dir>/reports/`，文件名 `troas_YYYY-MM-DD.csv`）
