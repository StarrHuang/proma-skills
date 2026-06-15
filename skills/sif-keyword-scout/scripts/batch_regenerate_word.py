"""
batch_regenerate_word.py  [开发/批跑专用，Agent 主流程不直接调用]

两种模式：
  1. 默认：从已有 *_stats_*.json 生成 insights_*.md 并重建 Word（脚本改版后修复旧输出）
  2. --full-pipeline：跑完三表 skip-word → insights → Word → history → Skill2（本地批跑测试）

用法 1：
  python batch_regenerate_word.py \\
    --result-dir ".../处理结果" --asin B0XXX --date 20260611 \\
    --stage 新品期 --category 沙发套 --scripts-dir "sif-keyword-scout/scripts"

用法 2：
  python batch_regenerate_word.py --full-pipeline \\
    --output-root ".../test" --asin B0XXX --date 20260611 \\
    --stage 新品期 --category 沙发套
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from report_utils import render_cross_reviews, render_t1_keyword_reviews, fmt_share_pct, is_missing

SCRIPTS = Path(__file__).resolve().parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def load(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_t1(d: dict, path: Path, category: str):
    lc = d.get("level_counts", {})
    th = d.get("thresholds", {})
    stage = d.get("stage", "")
    conc_med = th.get("conc_median") or 0.3
    reviews = render_t1_keyword_reviews(d.get("top_sa_keywords", []), stage, conc_med, 5)
    text = f"""## 执行摘要
ASIN {d.get('asin')}，{stage}，类目{category}。共 {d.get('total_keywords', 0)} 个调研词。
分层：S级 {lc.get('S级', 0)} / A级 {lc.get('A级', 0)} / B级 {lc.get('B级', 0)} / C级 {lc.get('C级', 0)}。
自动门槛 S≥{th.get('s_search_volume')}、A≥{th.get('a_search_volume')}；竞价中位 ${th.get('bid_median')}，集中度中位 {conc_med}。

## S/A 级投放策略（{stage}）
- **S级 {lc.get('S级', 0)} / A级 {lc.get('A级', 0)}**：可投池有限，新品期优先验证转化，再加大词预算
- **与交叉词单对齐**：表1 大词不等于 PD 主攻；最终以 SS/SSS 交叉结果分配预算
- **C 级 {lc.get('C级', 0)} 个**：默认否定，搜索词报告出现有效转化再评估

## TOP5 重点词点评
{reviews}

## PD 备战前 2 周行动清单
- **第 1 周**：TOP5 中选 3~5 个与 listing 规格一致的词，按上表匹配方式建组
- **第 2 周**：暂停 ACOS>150% 的词；转化词迁入「PD 加码组」
- **PD 前 3 天**：交叉 SS/SSS 词单独活动，预算不低于 SP 总预算 30%
- **PD 当天**：主攻组 budget +30%~50%，每小时看库存与 ACOS
"""
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_t2(d: dict, path: Path):
    lines = []
    # 字段名与 build_t2_stats 保持一致：top_opportunity_keywords、high_opp、total
    for kw in d.get("top_opportunity_keywords", [])[:10]:
        keyword = kw.get("keyword", "")
        diff    = kw.get("difficulty", "")
        nat_st  = kw.get("nat_status", "")
        lines.append(
            f"- **{keyword}**（难度 {diff}，自然位状态 {nat_st}）："
            f"竞品该词{'自然位未稳' if '未稳' in str(nat_st) or '纯广告' in str(nat_st) else '排名一般'}，"
            f"建议 PD 前 {'精准' if diff == '低' else '词组'}匹配试投，转化后加码。"
        )
    opp_block = "\n".join(lines) if lines else "- （无高机会词）"
    total = d.get("total", d.get("total_keywords", 0))

    text = f"""## 竞品流量结构弱点
共 {total} 个流量词；增长词 {d.get('growth_count', 0)} 个；高机会 {d.get('high_opp', 0)} 个。
纯广告/自然位未稳：{d.get('pure_ad_count', 0)}/{total}——竞品依赖 SP，广告抢位窗口大。

## TOP10 高机会词抢位策略
{opp_block}

## PD 前广告活动搭建方案
- **活动 A**：高机会+低难度 → 精准匹配，每词一组
- **活动 B**：高机会+中难度 → 词组试投
- **T-3**：转化词 bid +15~20%；无效词暂停
"""
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_t3(d: dict, path: Path, category: str):
    lines = []
    for kw in d.get("top_gap_keywords", [])[:8]:
        name = kw.get("keyword", "")
        sv = kw.get("search_volume", "")
        sp_raw = kw.get("sp_share_pct", kw.get("sp_share", ""))
        sp = "" if is_missing(sp_raw) else fmt_share_pct(sp_raw)
        sp_part = f"，SP份额 {sp}" if sp else ""
        lines.append(
            f"- **{name}**（搜索量 {sv}{sp_part}）：竞品广告覆盖不足，"
            f"若与「{category}」listing 语义一致，PD 前精准匹配抢位；否则标记不相关否投。"
        )
    gap_block = "\n".join(lines) if lines else "- （无缺口词）"
    text = f"""## 缺口词战略价值
类目「{category}」共 {d.get('total', d.get('total_keywords', 0))} 个广告词；缺口词 {d.get('gap_count', 0)} 个，低难度 {d.get('gap_low_difficulty', 0)} 个，防守词 {d.get('defense_count', 0)} 个。
{d.get('defense_note', '')}

## TOP 缺口词抢位建议
{gap_block}

## PD 备战行动清单
- **第 1 周**：语义匹配的 TOP 缺口词各开 1 精准组
- **第 2 周**：合并转化词，否掉偏离类目词
"""
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_cross(d: dict, path: Path):
    sss, ss, s = d.get("sss_count", 0), d.get("ss_count", 0), d.get("s_count", 0)
    focus = "SSS+SS" if sss else "SS"
    reviews = render_cross_reviews(d.get("primary_keywords", []), 10)
    text = f"""## 执行摘要
三表交叉：SSS {sss} / SS {ss} / S {s}。PD 主攻以 **{focus} 级** 为核心（{d.get('primary_focus_count', ss + sss)} 个词）。

## 交叉分级说明
- S 级 {s} 个为单表观察池，勿与表1 S/A 混淆
- 预算应集中在下列 {focus} 级词

## 主攻词逐条建议
{reviews}

## PD 备战行动清单
- **第 1 周**：{focus} 级词按上表匹配方式建组
- **第 2 周**：S 级仅观察，不加主预算
- **PD 当天**：主攻组提 budget 20%~50%
"""
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_tracker(d: dict, path: Path) -> None:
    s = d.get("summary", {})
    note = d.get("compare_note", "")
    ss_new = d.get("ss_new_list", [])[:10]
    ss_removed = d.get("ss_removed_list", [])[:10]
    sv_lines = [
        f"- **{x['关键词']}**（{x['级别']}）：搜索量 {x['上次搜索量']}→{x['本次搜索量']}（{x['变化%']}% {x['方向']}）"
        for x in d.get("sv_changed", [])[:8]
    ]
    text = f"""## 执行摘要
对比窗口：{note}。上次词池 {s.get('prev_total', 0)} 个，本次 {s.get('curr_total', 0)} 个。
新增 {s.get('new_total', 0)} / 消失 {s.get('removed_total', 0)}；SS 级新增 {s.get('ss_new', 0)}、稳定 {s.get('ss_stable', 0)}、掉出 {s.get('ss_removed', 0)}。

## 新增 SS 级词（建议评估是否加预算）
{chr(10).join('- **' + w + '**' for w in ss_new) if ss_new else '- （无新增 SS 级）'}

## 掉出 SS 级词（建议暂停或降价观察）
{chr(10).join('- **' + w + '**' for w in ss_removed) if ss_removed else '- （无掉出 SS 级）'}

## 搜索量显著变动（>20%）
{chr(10).join(sv_lines) if sv_lines else '- （无显著变动）'}

## 本周投放调整行动清单
- 对新增 SS 级词：有 listing 匹配则开精准组小预算试投
- 对掉出 SS/S 级词：暂停或降 bid 20%，观察 7 天
- 搜索量上涨词：转化稳定则 bid +10~15%
- 搜索量下跌词：先控 ACOS，无效则否词
"""
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _run_cmd(cmd: list[str], label: str) -> None:
    print(f"\n{'='*60}\n▶ {label}\n{'='*60}")
    r = subprocess.run(cmd, env=ENV, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {label} (exit {r.returncode})")


def run_full_pipeline(output_root: str, asin: str, date: str, stage: str, category: str,
                        product_type: str = "非标品") -> None:
    root = Path(output_root)
    raw = root / asin / date / "原始数据"
    res = root / asin / date / "处理结果"
    res.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    s = str(SCRIPTS)

    for name in (f"关键词调研_{date}.xlsx", f"反查流量词_{date}.xlsx", f"查广告词_{date}.xlsx"):
        if not (raw / name).is_file():
            raise FileNotFoundError(f"缺少原始表：{raw / name}")

    pt_args = ["--product-type", product_type, "--stage", stage]
    _run_cmd([py, f"{s}/process_table1.py", "--mode", "process",
              "--input", str(raw / f"关键词调研_{date}.xlsx"), "--output-dir", str(res),
              "--asin", asin, "--date", date, *pt_args, "--skip-word"], f"{asin} 表1")
    _run_cmd([py, f"{s}/process_table2.py", "--input", str(raw / f"反查流量词_{date}.xlsx"),
              "--output-dir", str(res), "--asin", asin, "--date", date, *pt_args, "--skip-word"], f"{asin} 表2")
    _run_cmd([py, f"{s}/process_table3.py", "--input", str(raw / f"查广告词_{date}.xlsx"),
              "--output-dir", str(res), "--asin", asin, "--date", date,
              "--product-category", category, *pt_args, "--skip-word"], f"{asin} 表3")
    _run_cmd([py, f"{s}/cross_analysis.py",
              "--t1", str(res / f"{asin}_关键词分层分析_{date}.xlsx"),
              "--t2", str(res / f"{asin}_竞品弱点分析_{date}.xlsx"),
              "--t3", str(res / f"{asin}_竞品缺口分析_{date}.xlsx"),
              "--output-dir", str(res), "--asin", asin, "--date", date, "--skip-word"], f"{asin} 交叉")

    main(output_root="", result_dir=str(res), asin=asin, date=date, stage=stage,
         category=category, product_type=product_type, scripts_dir=s, only=set())

    _run_cmd([py, f"{s}/update_history.py", "--output-dir", str(root),
              "--asin", asin, "--date", date, "--run-path", f"{asin}/{date}"], f"{asin} 历史")

    hist = subprocess.run(
        [py, f"{s}/check_history.py", "--asin", asin, "--output-dir", str(root), "--curr-date", date],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV,
    )
    info = json.loads(hist.stdout)
    if info.get("run_count", 0) >= 2 and info.get("compare_prev_run_path"):
        tracker = SCRIPTS.parent.parent / "sif-keyword-tracker" / "scripts" / "compare_versions.py"
        _run_cmd([py, str(tracker), "--auto", "--output-root", str(root), "--output-dir", str(res),
                  "--asin", asin, "--curr-date", date, "--skip-word"], f"{asin} Skill2 stats")
        sp = res / f"{asin}_tracker_stats_{date}.json"
        write_tracker(json.loads(sp.read_text(encoding="utf-8")), res / "insights_tracker.md")
        _run_cmd([py, str(tracker), "--auto", "--output-root", str(root), "--output-dir", str(res),
                  "--asin", asin, "--curr-date", date,
                  "--insights-file", str(res / "insights_tracker.md")], f"{asin} Skill2 Word")


def run_word(script: Path, args: list[str]):
    r = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=ENV,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        raise SystemExit(r.returncode)
    if r.stdout:
        print(r.stdout.splitlines()[-1])


def main(output_root="", result_dir="", asin="", date="", stage="新品期",
         category="", product_type="非标品", scripts_dir="", only=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--full-pipeline", action="store_true", help="跑完整 Skill1+2 批处理")
    ap.add_argument("--output-root", default="", help="--full-pipeline 时：output_dir 根目录")
    ap.add_argument("--result-dir", default="")
    ap.add_argument("--asin", required=False, default="")
    ap.add_argument("--date", required=False, default="")
    ap.add_argument("--stage", default="新品期")
    ap.add_argument("--category", default="")
    ap.add_argument("--product-type", default="非标品", choices=["标品", "非标品"])
    ap.add_argument("--scripts-dir", default="")
    ap.add_argument("--only", default="", help="t1,t2,t3,cross 逗号分隔，默认全部")
    args = ap.parse_args() if not result_dir else argparse.Namespace(
        full_pipeline=False, output_root=output_root, result_dir=result_dir,
        asin=asin, date=date, stage=stage, category=category, product_type=product_type,
        scripts_dir=scripts_dir or str(SCRIPTS), only=",".join(sorted(only or {"t1","t2","t3","cross"})),
    )

    if args.full_pipeline:
        if not args.output_root or not args.asin or not args.date:
            print("ERROR: --full-pipeline 需要 --output-root --asin --date", file=sys.stderr)
            sys.exit(1)
        run_full_pipeline(args.output_root, args.asin, args.date, args.stage,
                        args.category or "产品", args.product_type)
        print(f"\n✅ {args.asin} 全流程完成")
        return

    if not args.result_dir or not args.asin or not args.date or not args.scripts_dir:
        print("ERROR: 需要 --result-dir --asin --date --scripts-dir", file=sys.stderr)
        sys.exit(1)

    res = Path(args.result_dir)
    scripts = Path(args.scripts_dir)
    asin, date = args.asin, args.date
    cat = args.category or "产品"
    only = {x.strip() for x in args.only.split(",") if x.strip()} or {"t1", "t2", "t3", "cross"}

    raw = res.parent / "原始数据"

    if "t1" in only:
        t1_path = res / f"{asin}_t1_stats_{date}.json"
        pt = ["--product-type", args.product_type, "--stage", args.stage]
        if not t1_path.exists():
            run_word(scripts / "process_table1.py", [
                "--mode", "process", "--input", str(raw / f"关键词调研_{date}.xlsx"),
                "--output-dir", str(res), "--asin", asin, "--date", date,
                *pt, "--skip-word",
            ])
        t1 = load(t1_path)
        write_t1({**t1, "stage": args.stage}, res / "insights_t1.md", cat)
        run_word(scripts / "process_table1.py", [
            "--mode", "process", "--input", str(raw / f"关键词调研_{date}.xlsx"),
            "--output-dir", str(res), "--asin", asin, "--date", date,
            *pt, "--insights-file", str(res / "insights_t1.md"),
        ])

    if "t2" in only and (res / f"{asin}_t2_stats_{date}.json").exists():
        write_t2(load(res / f"{asin}_t2_stats_{date}.json"), res / "insights_t2.md")
        run_word(scripts / "process_table2.py", [
            "--input", str(raw / f"反查流量词_{date}.xlsx"),
            "--output-dir", str(res), "--asin", asin, "--date", date,
            "--product-type", args.product_type, "--stage", args.stage,
            "--insights-file", str(res / "insights_t2.md"),
        ])

    if "t3" in only and (res / f"{asin}_t3_stats_{date}.json").exists():
        write_t3(load(res / f"{asin}_t3_stats_{date}.json"), res / "insights_t3.md", cat)
        run_word(scripts / "process_table3.py", [
            "--input", str(raw / f"查广告词_{date}.xlsx"),
            "--output-dir", str(res), "--asin", asin, "--date", date,
            "--product-category", cat,
            "--product-type", args.product_type, "--stage", args.stage,
            "--insights-file", str(res / "insights_t3.md"),
        ])

    if "cross" in only and (res / f"{asin}_cross_stats_{date}.json").exists():
        write_cross(load(res / f"{asin}_cross_stats_{date}.json"), res / "insights_cross.md")
        run_word(scripts / "cross_analysis.py", [
            "--t1", str(res / f"{asin}_关键词分层分析_{date}.xlsx"),
            "--t2", str(res / f"{asin}_竞品弱点分析_{date}.xlsx"),
            "--t3", str(res / f"{asin}_竞品缺口分析_{date}.xlsx"),
            "--output-dir", str(res), "--asin", asin, "--date", date,
            "--insights-file", str(res / "insights_cross.md"),
        ])

    print(f"Done: {res} ({','.join(sorted(only))})")


if __name__ == "__main__":
    main()  # noqa: 供 CLI 与 run_full_pipeline 内部调用
