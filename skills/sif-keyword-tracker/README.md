# sif-keyword-tracker

Sif 关键词历史跟踪 skill。通常由 `sif-keyword-scout` 在同一 ASIN 有历史记录时自动触发，按 1-7 天窗口对比两期 PD 主攻词单，输出新增/消失/稳定词变化和投放建议 Word 报告。

## 使用方式

优先从 `sif-keyword-scout` 触发；单独运行时需要提供同级的 `sif-keyword-scout` scripts、`.sif-config.json` 中的 `output_dir`，以及当前 ASIN / 数据日期。

```bash
python "sif-keyword-tracker/scripts/compare_versions.py" \
  --auto \
  --output-root "{output_dir}" \
  --output-dir "{result_dir}" \
  --asin "{ASIN}" \
  --curr-date "{YYYYMMDD}" \
  --skip-word
```

Agent 必须先解读变化并获得用户确认，再写 `insights_tracker.md` 并生成最终 Word 报告。完整流程见 `SKILL.md`。
