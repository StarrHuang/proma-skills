"""
stdio_utf8.py - Windows GBK 控制台兼容

问题：Windows 默认控制台编码为 GBK，脚本 print 含 emoji（📂✅ 等）会触发
UnicodeEncodeError，导致 Agent/Kimi 直接调用 Python 时表1 等步骤失败。

用法：各入口脚本首行 import stdio_utf8 即可（导入时自动修复 stdout/stderr）。
备选：调用方设置环境变量 PYTHONIOENCODING=utf-8（subprocess 场景）。
"""
from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    """将 stdout/stderr 重配置为 UTF-8，无法编码的字符用 replace 兜底。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            enc = (getattr(stream, "encoding", None) or "").lower()
            if enc not in ("utf-8", "utf8"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


ensure_utf8_stdio()
