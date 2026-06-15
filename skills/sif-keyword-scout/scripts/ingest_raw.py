"""
ingest_raw.py - 初始化目录 + 接入用户提供的原始表（任意路径/文件名）

用法 1（仅建目录）：
  python ingest_raw.py --asin B0CRMP3RQT --output-dir "D:/out" --stage 成长期 --product-category 水杯

用法 2（用户直接给三个文件路径）：
  python ingest_raw.py --asin B0CRMP3RQT --output-dir "D:/out" \
    --t1 "D:/Downloads/Sif关键词调研-US-xxx.xlsx" \
    --t2 "D:/Downloads/asinKeywords_xxx.xlsx" \
    --t3 "D:/Downloads/asinAdKwView_xxx.xlsx"

用法 3（给一个文件夹，自动识别三张表）：
  python ingest_raw.py --asin B0CRMP3RQT --output-dir "D:/out" --from-dir "D:/Downloads"

stdout 输出 JSON（含 raw_dir / result_dir / 标准文件名路径），供后续 process_* 使用。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from run_context import init_run

try:
    import pandas as pd
except ImportError:
    print("请安装 pandas: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

T1_MARKERS = ["周搜索量", "Top3集中度", "Top3点击集中度", "相关性得分", "ABA排名"]
T2_MARKERS = ["流量词占比", "自然流量占比", "广告流量占比", "是否增长词"]
T3_MARKERS = ["广告搜索词", "SP广告流量份额", "该Listing在该词下的SP广告流量份额", "贡献占比"]


def _cols_in_file(path: Path) -> set[str]:
    found: set[str] = set()
    try:
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names[:5]:
            for header in (0, 1):
                try:
                    df = pd.read_excel(path, sheet_name=sheet, header=header, nrows=3)
                    found.update(str(c) for c in df.columns)
                except Exception:
                    continue
    except Exception:
        pass
    return found


def _score_table(path: Path) -> dict[str, int]:
    name = path.name.lower()
    cols = _cols_in_file(path)
    col_text = " ".join(cols)
    scores = {"t1": 0, "t2": 0, "t3": 0}
    for m in T1_MARKERS:
        if m in col_text:
            scores["t1"] += 2
    for m in T2_MARKERS:
        if m in col_text:
            scores["t2"] += 2
    for m in T3_MARKERS:
        if m in col_text:
            scores["t3"] += 2
    if "关键词调研" in name or "keywords-library" in name or "sif关键词调研" in name:
        scores["t1"] += 3
    if "asinkeywords" in name or "反查流量词" in name or "流量词" in name:
        scores["t2"] += 3
    if "asinadkwview" in name or "查广告词" in name or "adxray" in name:
        scores["t3"] += 3
    if "广告搜索词" in col_text:
        scores["t3"] += 4
    if "流量词占比" in col_text:
        scores["t2"] += 4
    if "周搜索量" in col_text and "相关性" in col_text:
        scores["t1"] += 4
    return scores


def detect_table_type(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"找不到文件：{path}")
    scores = _score_table(p)
    best = max(scores, key=scores.get)
    if scores[best] < 2:
        raise ValueError(f"无法识别表类型：{path}（列特征不足，请用 --t1/--t2/--t3 显式指定）")
    return best


def _collect_paths(t1: str, t2: str, t3: str, from_dir: str) -> list[str]:
    explicit = [p for p in (t1, t2, t3) if p]
    if explicit and from_dir:
        raise ValueError("不要同时使用 --from-dir 与 --t1/--t2/--t3")
    if from_dir:
        d = Path(from_dir)
        if not d.is_dir():
            raise FileNotFoundError(f"找不到目录：{from_dir}")
        return [str(p) for p in d.iterdir() if p.suffix.lower() in (".xlsx", ".xls")]
    return explicit


def ingest_files(
    ctx: dict,
    sources: dict[str, str],
) -> dict:
    """sources: {t1: path, t2: path, t3: path} → 复制到 raw_dir 标准命名"""
    raw_dir = Path(ctx["raw_dir"])
    rid = ctx["run_id"]
    targets = {
        "t1": raw_dir / f"关键词调研_{rid}.xlsx",
        "t2": raw_dir / f"反查流量词_{rid}.xlsx",
        "t3": raw_dir / f"查广告词_{rid}.xlsx",
    }
    ingested = {}
    for key, src in sources.items():
        src_p = Path(src).resolve()
        dst_p = targets[key].resolve()
        if not src_p.is_file():
            raise FileNotFoundError(f"找不到 {key} 文件：{src}")
        if src_p != dst_p:
            shutil.copy2(src_p, dst_p)
        ingested[key] = {
            "source": str(src_p),
            "target": str(dst_p),
            "skipped_copy": src_p == dst_p,
        }
    ctx["ingested"] = ingested
    ctx["raw_paths"] = {k: str(v) for k, v in targets.items()}
    return ctx


def auto_map_files(paths: list[str]) -> dict[str, str]:
    """自动识别三张表；若用户已用 --t1/--t2/--t3 则直接映射"""
    mapping: dict[str, str] = {}
    unknown: list[str] = []

    for p in paths:
        try:
            kind = detect_table_type(p)
        except ValueError:
            unknown.append(p)
            continue
        if kind in mapping:
            # 同类型取特征分更高的
            if _score_table(Path(p))[kind] > _score_table(Path(mapping[kind]))[kind]:
                unknown.append(mapping[kind])
                mapping[kind] = p
            else:
                unknown.append(p)
        else:
            mapping[kind] = p

    missing = [k for k in ("t1", "t2", "t3") if k not in mapping]
    if missing:
        msg = f"缺少表：{', '.join(missing)}"
        if unknown:
            msg += f"；未识别文件：{unknown}"
        raise ValueError(msg)
    return mapping


def main():
    parser = argparse.ArgumentParser(description="建目录 + 接入用户原始表（任意路径）")
    parser.add_argument("--asin", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--date", default="", help="YYYYMMDD，默认今天")
    parser.add_argument("--stage", default="")
    parser.add_argument("--product-category", default="")
    parser.add_argument("--product-type", default="", choices=["", "标品", "非标品"],
                        help="标品/非标品门槛预设，空则默认非标品")
    parser.add_argument("--t1", default="", help="表1 文件路径（关键词调研）")
    parser.add_argument("--t2", default="", help="表2 文件路径（反查流量词）")
    parser.add_argument("--t3", default="", help="表3 文件路径（查广告词）")
    parser.add_argument("--from-dir", default="", help="含三张 xlsx 的文件夹，自动识别")
    args = parser.parse_args()

    extra = {}
    if args.stage:
        extra["stage"] = args.stage
    if args.product_category:
        extra["product_category"] = args.product_category
    if args.product_type:
        extra["product_type"] = args.product_type

    ctx = init_run(args.output_dir, args.asin, date=args.date or None, extra=extra or None)

    paths = _collect_paths(args.t1, args.t2, args.t3, args.from_dir)
    if paths:
        if args.t1 and args.t2 and args.t3:
            mapping = {"t1": args.t1, "t2": args.t2, "t3": args.t3}
        else:
            mapping = auto_map_files(paths)
        ctx = ingest_files(ctx, mapping)
        print(f"✅ 已接入原始表 → {ctx['raw_dir']}", file=sys.stderr)
        for k, info in ctx["ingested"].items():
            print(f"   {k}: {Path(info['source']).name} → {Path(info['target']).name}", file=sys.stderr)
    else:
        print(f"📁 已创建目录（待放入原始表）：{ctx['raw_dir']}", file=sys.stderr)

    print(json.dumps(ctx, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
