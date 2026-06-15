"""
resolve_workspace.py - 解析 Sif 工作区路径（供 Agent 首次初始化使用）

发现顺序：
1. 环境变量 SIF_WORKSPACE
2. 从当前目录向上查找 .sif-config.json
3. 从本脚本所在 skill 目录向上查找 .sif-config.json（最多 5 层）
4. 均未找到 → workspace_found=false，需询问用户

用法：
  python resolve_workspace.py
  python resolve_workspace.py --init-output-dir "D:\\your\\output"
  python resolve_workspace.py --init-download-dir "C:\\Users\\you\\Downloads"
"""
import argparse
import json
import os
import sys
from pathlib import Path

import stdio_utf8  # noqa: F401 — Windows GBK 控制台 UTF-8 兼容

from threshold_presets import load_config_product_type

CONFIG_NAME = ".sif-config.json"
EXAMPLE_NAME = ".sif-config.example.json"


def find_config(start: Path, max_up: int = 6):
    cur = start.resolve()
    for _ in range(max_up):
        candidate = cur / CONFIG_NAME
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def load_or_create_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def sibling(skill_root: Path, name: str) -> Path:
    return skill_root.parent / name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-output-dir", default="")
    parser.add_argument("--init-download-dir", default="")
    parser.add_argument("--init-sif-url", default="")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    workspace = os.environ.get("SIF_WORKSPACE", "").strip()

    config_path = None
    if workspace:
        p = Path(workspace) / CONFIG_NAME
        if p.is_file():
            config_path = p
    if not config_path:
        config_path = find_config(Path.cwd()) or find_config(skill_root)

    if not config_path:
        # 尝试在 skill 父目录创建配置（典型布局：sif-skills/.sif-config.json）
        default_ws = skill_root.parent
        example = default_ws / EXAMPLE_NAME
        target = default_ws / CONFIG_NAME
        if not target.is_file() and example.is_file():
            import shutil
            shutil.copy(example, target)
            config_path = target

    if not config_path:
        out = {
            "workspace_found": False,
            "message": "未找到 .sif-config.json，请设置 SIF_WORKSPACE 或指定 output_dir 初始化",
            "skill_scout": str(skill_root),
            "skill_tracker": str(sibling(skill_root, "sif-keyword-tracker")),
            "web_access": str(sibling(skill_root, "web-access")),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(2)

    cfg = load_or_create_config(config_path)
    changed = False
    if args.init_output_dir:
        cfg["output_dir"] = args.init_output_dir
        changed = True
    if args.init_download_dir:
        cfg["download_dir"] = args.init_download_dir
        changed = True
    if args.init_sif_url:
        cfg["sif_url"] = args.init_sif_url
        changed = True
    if changed:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    ws = config_path.parent
    scout = ws / "sif-keyword-scout"
    if not scout.is_dir():
        scout = skill_root

    result = {
        "workspace_found": True,
        "workspace": str(ws),
        "config_path": str(config_path),
        "output_dir": cfg.get("output_dir", ""),
        "download_dir": cfg.get("download_dir", ""),
        "sif_url": cfg.get("sif_url", ""),
        "default_product_type": load_config_product_type(config_path),
        "threshold_presets_doc": "sif-keyword-scout/references/threshold-presets.md",
        "skill_scout": str(scout),
        "skill_tracker": str(ws / "sif-keyword-tracker"),
        "web_access": str(ws / "web-access"),
        "scripts": {
            "resolve_workspace": str(scout / "scripts" / "resolve_workspace.py"),
            "ingest_raw": str(scout / "scripts" / "ingest_raw.py"),
            "check_history": str(scout / "scripts" / "check_history.py"),
            "process_table1": str(scout / "scripts" / "process_table1.py"),
            "process_table2": str(scout / "scripts" / "process_table2.py"),
            "process_table3": str(scout / "scripts" / "process_table3.py"),
            "cross_analysis": str(scout / "scripts" / "cross_analysis.py"),
            "update_history": str(scout / "scripts" / "update_history.py"),
            "batch_regenerate_word": str(scout / "scripts" / "batch_regenerate_word.py"),
            "compare_versions": str(ws / "sif-keyword-tracker" / "scripts" / "compare_versions.py"),
        },
        "needs_output_dir": not bool(cfg.get("output_dir")),
        "needs_download_dir": not bool(cfg.get("download_dir")),
    }
    needs = result["needs_output_dir"] or result["needs_download_dir"]
    if needs or not cfg.get("output_dir"):
        result["first_time_guide"] = {
            "doc": "sif-keyword-scout/references/first-time-setup.md",
            "agent_must_read": True,
            "steps": [],
        }
        guide = result["first_time_guide"]["steps"]
        if result["needs_output_dir"]:
            guide.append({
                "id": "output_dir",
                "required": True,
                "prompt": "请用户提供「报告输出根目录」完整路径（所有 ASIN 共用，只配置一次）。禁止擅自填写他人路径。详见 sif-keyword-scout/references/first-time-setup.md",
                "command": f'python "{scout / "scripts" / "resolve_workspace.py"}" --init-output-dir "{{USER_PATH}}"',
            })
        if result["needs_download_dir"]:
            guide.append({
                "id": "download_dir",
                "required": False,
                "when": "仅方式 B 浏览器导出需要",
                "prompt": "请用户提供浏览器默认下载文件夹路径。",
                "command": f'python "{scout / "scripts" / "resolve_workspace.py"}" --init-download-dir "{{USER_PATH}}"',
            })
        if not result["needs_output_dir"] and cfg.get("output_dir"):
            result["first_time_guide"]["note"] = "output_dir 已配置；若用户要更换，使用 --init-output-dir"
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
