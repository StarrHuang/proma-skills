"""
threshold_presets.py - 标品/非标品默认门槛 + CLI 覆盖合并

用法：
  params = resolve_thresholds("非标品", stage="新品期", overrides={"sv_threshold": 1000})
  params = resolve_thresholds("标品", overrides={"s_conc_max": 0.32})
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PRODUCT_TYPES = ("标品", "非标品")
CONFIG_NAME = ".sif-config.json"

# 与 Sif关键词（6.11）Prompt 1~3 对齐；Agent 可在暂停点用 CLI 覆盖单项
PRESETS: dict[str, dict[str, Any]] = {
    "标品": {
        "s_percentile": 97,
        "a_percentile": 85,
        "s_conc_max": 0.30,
        "a_conc_max": 0.35,
        "s_bid_mult": 1.2,
        "a_bid_mult": 1.5,
        "b_require_cvr": True,
        "t2_opp_conc_max": 0.45,
        "t2_enter_low_conc": 0.25,
        "t2_enter_high_conc": 0.40,
        "t2_pure_ad_nat_max": 0.20,
        "sv_threshold": 3000,
        "gap_share_max": 5.0,
        "defense_share_min": 20.0,
    },
    "非标品": {
        "s_percentile": 97,
        "a_percentile": 85,
        "s_conc_max": 0.25,
        "a_conc_max": 0.35,
        "s_bid_mult": 1.2,
        "a_bid_mult": 1.5,
        "b_require_cvr": False,
        "t2_opp_conc_max": 0.40,
        "t2_enter_low_conc": 0.25,
        "t2_enter_high_conc": 0.40,
        "t2_pure_ad_nat_max": 0.20,
        "sv_threshold": 2000,
        "gap_share_max": 5.0,
        "defense_share_min": 20.0,
    },
}

# CLI 名 → 预设字段
CLI_OVERRIDES = {
    "s_threshold": None,  # 表1 搜索量门槛，单独处理
    "a_threshold": None,
    "s_conc_max": "s_conc_max",
    "a_conc_max": "a_conc_max",
    "s_bid_mult": "s_bid_mult",
    "a_bid_mult": "a_bid_mult",
    "sv_threshold": "sv_threshold",
    "gap_share_max": "gap_share_max",
    "defense_share_min": "defense_share_min",
    "t2_opp_conc_max": "t2_opp_conc_max",
    "t2_pure_ad_nat_max": "t2_pure_ad_nat_max",
}


def normalize_product_type(value: str | None, fallback: str = "非标品") -> str:
    v = (value or "").strip()
    if v in PRODUCT_TYPES:
        return v
    return fallback if fallback in PRODUCT_TYPES else "非标品"


def load_config_product_type(config_path: str | Path | None = None) -> str:
    if config_path is None:
        return "非标品"
    p = Path(config_path)
    if not p.is_file():
        return "非标品"
    try:
        with open(p, encoding="utf-8") as f:
            cfg = json.load(f)
        return normalize_product_type(cfg.get("default_product_type"))
    except Exception:
        return "非标品"


def resolve_thresholds(
    product_type: str,
    stage: str = "新品期",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """合并预设 + 阶段微调 + 用户覆盖。返回副本，可安全修改。"""
    pt = normalize_product_type(product_type)
    out = deepcopy(PRESETS[pt])
    out["product_type"] = pt
    out["stage"] = stage

    # 新品期：B 级转化率条件默认放宽（数据少）
    if stage == "新品期" and pt == "非标品":
        out["b_require_cvr"] = False
    elif stage == "新品期" and pt == "标品":
        out["b_require_cvr"] = False

    if overrides:
        for k, v in overrides.items():
            if v is None:
                continue
            if k in ("s_threshold", "a_threshold"):
                out[k] = int(v)
            elif k in out or k in CLI_OVERRIDES.values():
                out[k] = v
    return out


def add_product_type_arg(parser, default: str = "非标品"):
    parser.add_argument(
        "--product-type",
        default=default,
        choices=list(PRODUCT_TYPES),
        help="标品/非标品预设门槛（可被单项 --xxx 覆盖）",
    )


def collect_overrides_from_args(args) -> dict[str, Any]:
    """从 argparse Namespace 收集非空覆盖项。"""
    field_map = {
        "s_threshold": "s_threshold",
        "a_threshold": "a_threshold",
        "s_conc_max": "s_conc_max",
        "a_conc_max": "a_conc_max",
        "s_bid_mult": "s_bid_mult",
        "a_bid_mult": "a_bid_mult",
        "sv_threshold": "sv_threshold",
        "gap_share_max": "gap_share_max",
        "defense_share_min": "defense_share_min",
        "t2_opp_conc_max": "t2_opp_conc_max",
        "t2_pure_ad_nat_max": "t2_pure_ad_nat_max",
    }
    out: dict[str, Any] = {}
    for key, attr in field_map.items():
        if not hasattr(args, attr):
            continue
        v = getattr(args, attr)
        if v is None:
            continue
        if key in ("s_threshold", "a_threshold", "sv_threshold") and int(v) == 0:
            continue
        out[key] = v
    return out


def format_params_summary(params: dict[str, Any]) -> str:
    return (
        f"品类={params.get('product_type')} | "
        f"S集中度<{params.get('s_conc_max')} A<{params.get('a_conc_max')} | "
        f"表3搜索量>{params.get('sv_threshold')} 缺口<{params.get('gap_share_max')}% "
        f"防守>{params.get('defense_share_min')}%"
    )
