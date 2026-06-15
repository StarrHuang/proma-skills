---
name: bggg-tiktok-studio
description: >
  TikTok 视频全流程工作室 — 下载、分析、剪辑、AI修复、CapCut导出，一站式完成。
  四阶段管道：① 下载 (yt-dlp + tikwm兜底，支持单视频/博主主页/批量) →
  ② 分析 (ffprobe/whisper转写/关键帧/timeline/contact sheet/OCR/场景检测) →
  ③ 剪辑 (9:16竖屏重构/hook大字幕/BGM音频ducking/去空白/edit_plan/FFmpeg渲染final.mp4) →
  ④ 精修 (AI痕迹检测/RIFE补帧/CapCut草稿生成)。

  **触发词 (中文)**：TikTok视频下载、下载TT视频、TikTok去水印、批量下载博主作品、
  分析TikTok视频、看懂视频、读视频、视频总结、提取字幕、语音转文字、ASR、
  视频关键帧、视频timeline、剪辑TikTok、剪短视频、TikTok成片、AI视频二创、
  9:16重构、视频加字幕、BGM、hook overlay、CapCut草稿、AI痕迹检查、视频补帧、
  RIFE补帧、video edit plan、竖屏剪辑、短视频制作、口播剪辑、产品短片。

  **Trigger (EN)**: download TikTok video, TT downloader, TikTok no watermark,
  batch download TikTok, download creator videos, analyze TikTok video,
  understand video, read video, video summary, extract subtitles, speech to text,
  video ASR, keyframes, video timeline, edit TikTok, cut short video,
  TikTok edit, AI video remix, 9:16 reframe, add captions, BGM overlay,
  hook overlay, CapCut draft, AI artifact check, video frame interpolation,
  RIFE interpolation, video edit plan, vertical video edit, UGC ad edit.
version: "2.0.0"
user-invocable: true
compatibility: "Requires Python 3, ffmpeg, ffprobe, Node.js. Optional: faster-whisper or whisper CLI, yt-dlp, tesseract (OCR), RIFE (frame interpolation)."
---

# BGGG TikTok Studio

一站式 TikTok 视频工作台。下载 → 分析 → 剪辑 → 精修，四阶段管道。

**原则**：不要让 Codex 直接"看 mp4"——先把视频拆成可读、可搜索、可执行的上下文，再做判断和剪辑。

---

## 四阶段管道

```
Download  →  Analyze  →  Edit  →  Polish
(下载)       (分析)      (剪辑)     (精修)
```

用户可以选择从任意阶段开始。比如已有本地视频 → 直接跳到 Analyze；只需要下载 → 停在 Download。

---

## Phase 1: Download (下载)

```bash
python3 bggg-tiktok-studio/scripts/download_tiktok.py "<TikTok URL>"
```

**输入识别**：
- `/video/` 或 `/photo/` → 单个作品
- `@username` → 博主主页，`--limit N` 控制数量，`--limit 0` = 全部
- 需要登录态时传 `--cookies-browser chrome`

**常用命令**：

```bash
# 单视频
python3 bggg-tiktok-studio/scripts/download_tiktok.py "https://www.tiktok.com/@user/video/123" --thumbnail

# 博主前30条
python3 bggg-tiktok-studio/scripts/download_tiktok.py "https://www.tiktok.com/@user" --mode author --limit 30 --thumbnail

# 博主全部
python3 bggg-tiktok-studio/scripts/download_tiktok.py "https://www.tiktok.com/@user" --mode author --limit 0 --thumbnail
```

输出：`download_manifest.json`（含 `manifestPath`、`itemCount`、`items[].filePath`）。

---

## Phase 2: Analyze (分析)

```bash
python3 bggg-tiktok-studio/scripts/analyze_video.py "/path/to/video.mp4"
```

生成完整分析产物：
```
projects/YYYYMMDD_slug/
├── raw/input.mp4
├── analysis/
│   ├── metadata.json        # 时长/分辨率/编码/流信息
│   ├── transcript.txt       # 转写全文
│   ├── transcript.srt       # 时间轴字幕
│   ├── scenes.json          # 场景切分
│   ├── timeline.md          # 场景表 + 字幕摘要 + 关键帧路径
│   ├── contact_sheet.jpg    # 视觉全景
│   ├── keyframes/           # 逐场景关键帧
│   ├── audio_events.json    # 静音/音量事件
│   ├── ocr.json             # 画面文字
│   └── analysis_manifest.json
└── output/
    └── edit_plan.template.json
```

**阅读顺序**：manifest → metadata → contact_sheet → timeline → transcript → audio_events → ocr

**常用命令**：

```bash
# 完整分析
python3 bggg-tiktok-studio/scripts/analyze_video.py "/path/to/video.mp4" --slug my_project

# 快速纯视觉（跳过转写）
python3 bggg-tiktok-studio/scripts/analyze_video.py "/path/to/video.mp4" --no-transcribe --max-frames 24

# 指定模型 + 语言
python3 bggg-tiktok-studio/scripts/analyze_video.py "/path/to/video.mp4" --model small --language auto

# 仅转写（独立脚本）
python3 bggg-tiktok-studio/scripts/transcribe_video.py "/path/to/video-or-folder" --recursive --srt --json
```

---

## Phase 3: Edit (剪辑)

TikTok 默认参数：1080×1920、30fps、15-45s、前2s强hook、大字字幕、轻BGM。

### 3.1 初始化项目

```bash
python3 bggg-tiktok-studio/scripts/init_project.py "<project-dir>" --name "<name>" --inputs "<video1>" "<video2>"
```

### 3.2 探测素材

```bash
python3 bggg-tiktok-studio/scripts/probe_media.py "<project-dir>/raw" --out "<project-dir>/metadata/media_inventory.json" --frames-dir "<project-dir>/diagnostics/frames"
```

### 3.3 生成剪辑计划

```bash
python3 bggg-tiktok-studio/scripts/make_plan.py "<project-dir>" --title "<hook>" --target-seconds 30
```

### 3.4 渲染

```bash
python3 bggg-tiktok-studio/scripts/render_tiktok_cut.py "<project-dir>/plans/edit_plan.json"
```

### 3.5 自检

```bash
ffprobe -v error -show_entries stream=width,height,duration,codec_name -of csv=p=0 renders/final_tiktok.mp4
```

### Edit Plan 最小示例

```json
{
  "version": 1,
  "project": {"title": "TikTok cut", "platform": "tiktok", "target": {"width": 1080, "height": 1920, "fps": 30}},
  "settings": {"fit": "blur-bg", "grade": "punch", "caption_style": "tiktok-bold", "voice_volume": 1.0, "output_name": "final_tiktok.mp4"},
  "clips": [{"source": "raw/clip.mp4", "start": 0.0, "end": 6.2, "fit": "blur-bg", "label": "HOOK"}],
  "captions": [{"start": 0.0, "end": 2.4, "text": "This product changed everything", "style": "hook"}],
  "overlays": [{"start": 0.0, "end": 2.4, "text": "AI Video Remix", "style": "hook"}],
  "bgm": {"path": "assets/bgm/music.mp3", "volume": 0.12},
  "export": {"crf": 20, "preset": "fast"}
}
```

### 剪辑判断规则

- **前3s必须给理由**：强动作、结果预览、反差句、价格/痛点/卖点 overlay
- **竖屏重构默认 `blur-bg`**：主体大且稳定用 `cover`，需全图用 `contain`
- **字幕安全区**：中下区域，避开底部描述区和右侧操作栏。价格/CTA 放顶部或中部 badge
- **BGM 层次**：有口播时 0.08-0.14，纯视觉向 0.18-0.28
- **AI 视频优先删坏帧**：变形手、漂移 logo、字幕穿帮、闪帧、循环卡顿、主体出框

---

## Phase 4: Polish (精修)

### CapCut 草稿导出

```bash
node bggg-tiktok-studio/scripts/create-capcut-draft.mjs \
  --template "TEMPLATE_NAME" \
  --video "/path/to/video.mp4" \
  --name "my-draft" \
  --captions "Line 1\nLine 2\nLine 3"
```

CapCut 默认草稿目录：`$HOME/Movies/CapCut/User Data/Projects/com.lveditor.draft`

### AI 痕迹检测

```bash
# 单视频
node bggg-tiktok-studio/scripts/extract-ai-artifact-frames.mjs --video "/path/to/video.mp4" --output-root ./qa

# 批量
node bggg-tiktok-studio/scripts/extract-ai-artifact-frames.mjs --video-dir "/path/to/videos" --output-root ./qa
```

### 修复规划

```bash
node bggg-tiktok-studio/scripts/plan-ai-artifact-fixes.mjs --review ./ai_artifact_review.json --output ./fix_plan.json
```

### RIFE 补帧

```bash
node bggg-tiktok-studio/scripts/smart-frame-interpolate.mjs --input "/path/to/source.mp4" --output "/path/to/source_60fps_rife.mp4"
```

---

## 快捷场景

| 用户说 | 对应阶段 | 首步命令 |
|-------|---------|---------|
| "下载这个TikTok视频" | Phase 1 only | `download_tiktok.py <URL>` |
| "帮我看看这个视频讲了什么" | Phase 2 only | `analyze_video.py <path>` |
| "给这个视频加字幕" | Phase 2 → 3 | `transcribe_video.py` → 抄字幕进 edit_plan → 渲染 |
| "把这个剪成TikTok" | Phase 2 → 3 | 跑完整 analyze → make_plan → render |
| "这个AI视频有瑕疵帮我修" | Phase 4 | `extract-ai-artifact-frames.mjs` → `plan-ai-artifact-fixes.mjs` |
| "套CapCut模板导出" | Phase 4 | `create-capcut-draft.mjs` |
| "下载+分析+剪辑一条龙" | Phase 1 → 2 → 3 | 顺序跑完整管道 |

---

## 脚本清单

| 脚本 | 用途 | 来源 |
|------|------|------|
| `scripts/download_tiktok.py` | TikTok 视频下载 (yt-dlp + tikwm) | downloader |
| `scripts/analyze_video.py` | 视频完整分析 (ffprobe/whisper/场景/OCR) | readvideo |
| `scripts/transcribe_video.py` | 独立转写 (批量/递归/SRT/JSON) | readvideo |
| `scripts/init_project.py` | 剪辑项目初始化 | cut |
| `scripts/probe_media.py` | 素材探测 + 抽帧 | cut |
| `scripts/media_common.py` | 媒体工具共用库 | cut |
| `scripts/make_plan.py` | 自动生成 starter edit_plan | cut |
| `scripts/render_tiktok_cut.py` | FFmpeg 渲染 TikTok 成片 | cut |
| `scripts/transcribe.py` | 剪辑流程内转写 | cut |
| `scripts/create-capcut-draft.mjs` | CapCut 草稿生成 | capcut |
| `scripts/validate-capcut-draft.mjs` | CapCut 草稿结构验证 | capcut |
| `scripts/extract-template-styles.mjs` | CapCut 模板样式提取 | capcut |
| `scripts/extract-ai-artifact-frames.mjs` | AI 视频痕迹抽帧检测 | capcut |
| `scripts/plan-ai-artifact-fixes.mjs` | AI 痕迹修复窗口规划 | capcut |
| `scripts/smart-frame-interpolate.mjs` | 本地 RIFE 高质量补帧 | capcut |

详细参数按需读取 `references/` 下的对应文档。

---

## 交付格式

完成后给用户：
- 成片：`<project-dir>/renders/final_tiktok.mp4`
- 剪辑计划：`<project-dir>/plans/edit_plan.json`
- 渲染报告：`<project-dir>/renders/render_report.json`
- 字幕：`<project-dir>/captions/final_captions.ass`（如生成转写则含 SRT/JSON）
- 分析产物：`<project-dir>/analysis/timeline.md`、`contact_sheet.jpg`

如有未解决问题，明确列出：AI 画面不可修复变形、whisper 未安装、BGM 缺失、品牌合规需人工确认等。
