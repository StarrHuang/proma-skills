"""
run_context.py - 单次运行的日期路径与元数据

目录结构：
  {output_dir}/{ASIN}/{YYYYMMDD}/
    ├── 原始数据/
    └── 处理结果/
      └── charts/   （Word 生成后自动清理）

文件命名：关键词调研_{DATE}.xlsx（仅日期，不含时分）
历史记录表保留精确到分钟的时间戳，便于区分同日多次跑库。
"""
from __future__ import annotations

import stdio_utf8  # noqa: F401 — Windows GBK 控制台 UTF-8 兼容

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def run_id(date: str) -> str:
    """文件后缀用：20260611"""
    return date


def datetime_display(date: str, time: Optional[str] = None) -> str:
    """2026-06-11 或 2026-06-11 14:30"""
    base = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    if time:
        t = time.zfill(4)
        return f"{base} {t[:2]}:{t[2:4]}"
    return base


def relative_run_path(asin: str, date: str) -> str:
    """文件目录用：{ASIN}/{YYYYMMDD}"""
    return f"{asin}/{date}"


def history_run_path(asin: str, date: str, time: str) -> str:
    """历史表用：{ASIN}/{YYYYMMDD}/{HHmm}，区分同日多次跑库"""
    return f"{asin}/{date}/{time.zfill(4)}"


def build_run_dirs(output_dir: str, asin: str, date: str) -> dict:
    root = Path(output_dir) / asin / date
    raw_dir = root / "原始数据"
    result_dir = root / "处理结果"
    charts_dir = result_dir / "charts"
    for d in (raw_dir, result_dir, charts_dir):
        d.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    return {
        "output_dir": str(Path(output_dir).resolve()),
        "asin": asin,
        "date": date,
        "time": now.strftime("%H%M"),
        "run_id": run_id(date),
        "datetime_display": datetime_display(date, now.strftime("%H%M")),
        "run_path": relative_run_path(asin, date),
        "run_root": str(root.resolve()),
        "raw_dir": str(raw_dir.resolve()),
        "result_dir": str(result_dir.resolve()),
        "charts_dir": str(charts_dir.resolve()),
    }


def write_run_meta(ctx: dict, extra: Optional[dict] = None) -> str:
    meta = {
        "asin": ctx["asin"],
        "date": ctx["date"],
        "run_id": ctx["run_id"],
        "datetime_display": ctx["datetime_display"],
        "run_path": ctx["run_path"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    if extra:
        meta.update(extra)
    path = Path(ctx["run_root"]) / "run_meta.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return str(path)


def init_run(output_dir: str, asin: str, date: Optional[str] = None,
             extra: Optional[dict] = None) -> dict:
    now = datetime.now()
    date = date or now.strftime("%Y%m%d")
    ctx = build_run_dirs(output_dir, asin, date)
    ctx["meta_path"] = write_run_meta(ctx, extra)
    rid = ctx["run_id"]
    ctx["raw_files"] = {
        "t1": f"关键词调研_{rid}.xlsx",
        "t2": f"反查流量词_{rid}.xlsx",
        "t3": f"查广告词_{rid}.xlsx",
    }
    return ctx


def parse_run_path(path: str) -> dict:
    """解析 B0CRMP3RQT/20260611 或旧版带时分 B0CRMP3RQT/20260611/0244"""
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    out = {"asin": "", "date": "", "time": "", "legacy": True}
    if len(parts) >= 1:
        out["asin"] = parts[0]
    if len(parts) >= 2:
        out["date"] = parts[1]
    if len(parts) >= 3 and parts[2].isdigit():
        out["time"] = parts[2]
        out["legacy"] = False
    if out["date"]:
        out["run_id"] = out["date"]
        out["datetime_display"] = datetime_display(out["date"], out["time"] or None)
    return out


def result_dir_from_run_path(output_dir: str, run_path: str) -> str:
    # 兼容旧版含时分路径：始终落到 {asin}/{date}/处理结果
    info = parse_run_path(run_path)
    if info["asin"] and info["date"]:
        return str(Path(output_dir) / info["asin"] / info["date"] / "处理结果")
    return str(Path(output_dir) / run_path.replace("\\", "/") / "处理结果")
