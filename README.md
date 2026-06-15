# Proma Skills

> 224 个 Claude Code / Proma Agent Skills，覆盖跨境电商、飞书办公、数据分析、科学计算、内容创作、开发效率等场景。
>
> 每一个 skill 都是生产环境实战打磨出来的，供参考学习和直接安装使用。

## 这是什么？

**Skill** 是 Claude Code / Proma Agent 的可复用能力扩展。每个 skill 包含一个 `SKILL.md`（核心指令 + 触发规则），让 AI Agent 在特定场景下自动激活专业知识和工作流。

这个仓库汇集了我在日常工作（亚马逊自营品牌、Google Ads、SEO、投资研究）中沉淀的全部 skill，包括：

- 手动编写的自定义业务 skill
- 开源社区贡献的通用 skill
- 经过优化的第三方 skill

## 快速开始

### 前置条件

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 或 [Proma](https://github.com/Starr/Proma)
- 部分 skill 需要额外依赖（详见各 skill 的 SKILL.md 前置要求）

### 安装单个 Skill

```bash
# 复制到 Claude Code skills 目录
cp -r skills/<skill-name> ~/.claude/skills/

# 或复制到 Proma skill 目录
cp -r skills/<skill-name> ~/.proma/agent-workspaces/default/skills/
```

### 安装全部 Skills

```bash
git clone https://github.com/Starr/proma-skills.git
cp -r proma-skills/skills/* ~/.proma/agent-workspaces/default/skills/
```

## Skill 分类索引

### 亚马逊 & 电商 (7 个)

| Skill | 简介 |
|-------|------|
| `amazon-quality-investigation` | SPU 大货质量深度调查 — 拉取 ERP 质检/销量/评分/退货/利润/库存/采购/FBA 数据生成飞书报告 |
| `amazon-keyword-tiering` | 亚马逊关键词分层与投放策略 |
| `sif-keyword-scout` | Sif 关键词发现 — 基于 ASIN 反向挖掘竞品关键词 |
| `sif-keyword-tracker` | Sif 关键词动态跟踪 — 监控主攻词位变化，输出词库更新报告 |
| `sales-forecasting` | 销售与需求预测 — 统计/ML/DL/混合模型，特征工程，生产化部署 |
| `trendy-shopping` | Google Ads Shopping/PMax 趋势品分析，挖掘高潜力商品 |
| `troas-adjust` | Google Ads ROAS 目标调整策略 |

### 飞书 / Lark 集成 (23 个)

| Skill | 简介 |
|-------|------|
| `lark-mail` | 飞书邮箱 — 起草、发送、回复、转发、搜索邮件和管理草稿 |
| `lark-im` | 飞书即时通讯 — 收发消息、管理群聊、上传下载文件 |
| `lark-doc` | 飞书云文档 — 创建和编辑文档，支持 DocxXML/Markdown |
| `lark-sheets` | 飞书电子表格 — 创建表格、读写单元格、批量操作 |
| `lark-base` | 飞书多维表格 — 搜索 Base、字段管理、记录读写 |
| `lark-calendar` | 飞书日历 — 查看/创建日程、管理参会人、忙闲查询 |
| `lark-task` | 飞书任务 — 创建待办、拆分子任务、组织清单 |
| `lark-okr` | 飞书 OKR — 管理目标与关键结果 |
| `lark-minutes` | 飞书妙记 — 查询/下载会议录制和逐字稿 |
| `lark-vc` | 飞书视频会议 — 查询会议记录和纪要产物 |
| `lark-drive` | 飞书云空间 — 管理文件和文件夹、权限控制 |
| `lark-wiki` | 飞书知识库 — 管理知识空间、成员和文档节点 |
| `lark-approval` | 飞书审批 — 审批实例和任务管理 |
| `lark-attendance` | 飞书考勤 — 查询打卡记录 |
| `lark-contact` | 飞书通讯录 — 员工搜索和 Open ID 解析 |
| `lark-event` | 飞书事件订阅 — 流式消费 IM/群聊/表情反应事件 |
| `lark-markdown` | 飞书 Markdown 文件管理 |
| `lark-slides` | 飞书幻灯片 — 创建和编辑演示文稿 |
| `lark-whiteboard` | 飞书白板 |
| `lark-openapi-explorer` | 飞书原生 OpenAPI 探索 — 挖掘未封装的原生接口 |
| `lark-skill-maker` | 创建 lark-cli 自定义 Skill |
| `lark-shared` | 飞书 CLI 共享基础 — 认证登录、权限管理 |

**工作流 Skill：**

| Skill | 简介 |
|-------|------|
| `lark-workflow-meeting-summary` | 会议纪要整理 — 按时间范围汇总飞书会议生成结构化报告 |
| `lark-workflow-standup-report` | 日程待办摘要 — 编排日历和任务生成每日摘要 |

### 内容与媒体工具 — Baoyu 系列 (14 个)

| Skill | 简介 |
|-------|------|
| `baoyu-youtube-transcript` | YouTube 字幕/逐字稿下载 — 多语言、翻译、章节、说话人识别 |
| `baoyu-url-to-markdown` | 任意 URL 转 Markdown — Chrome CDP 驱动，支持登录态 |
| `baoyu-translate` | 多语言翻译 |
| `baoyu-image-gen` | AI 图像生成 — 多后端聚合（OpenAI/Azure/Google/FLUX 等） |
| `baoyu-wechat-summary` | 微信群聊摘要 — 结构化提取聊天精华 |
| `baoyu-xhs-images` | 小红书图片下载与管理 |
| `baoyu-diagram` | AI 图表生成 |
| `baoyu-comic` | AI 漫画生成 |
| `baoyu-infographic` | AI 信息图生成 |
| `baoyu-format-markdown` | Markdown 格式化 — 自动添加 frontmatter、标题、摘要 |
| `baoyu-compress-image` | 图片压缩 — WebP/PNG 自动选型 |
| `baoyu-electron-extract` | Electron 应用资源提取 — 解包 .asar，提取 JS/资源 |
| `baoyu-social-publisher` | 社交媒体发布 |
| `baoyu-danger-x-to-markdown` | X (Twitter) 推文/文章转 Markdown |

### TikTok 工具 — BGGG 系列 (4 个)

| Skill | 简介 |
|-------|------|
| `bggg-tiktok-search` | TikTok 调研与数据采集 — 搜索、浏览、截图、结构化导出 |
| `bggg-tiktok-studio` | TikTok 视频下载/分析/剪辑 |
| `bggg-creator-image2psd` | 创作者图片转 PSD |
| `bggg-skill-taotie` | Skill 进化器（饕餮）— 分析整合两个 skill 的优势 |

### 数据与分析 (7 个)

| Skill | 简介 |
|-------|------|
| `data-master` | 数据分析大师 — MECE 拆解 + 假设驱动 + Pyramid Principle 输出 |
| `metabase-card-review` | Metabase 看板优化 — SQL 审查、bug 检测、美化、冒烟测试 |
| `last30days` | 亚马逊近 30 天数据汇总分析 |
| `cider-postgresql-master` | PostgreSQL 数据查询与分析 |
| `database-lookup` | 78 个科学/生物医学/材料科学数据库搜索 |
| `exploratory-data-analysis` | 科学数据探索性分析 |
| `statistical-analysis` | 引导式统计分析 — 检验选择与报告 |

### 市场研究 & 报告 (2 个)

| Skill | 简介 |
|-------|------|
| `market-research-reports` | 市场研究报告生成（50+ 页，顶级咨询风格） |
| `men-tshirt-Moikrakki` | 男装 T 恤品牌分析 |

### 开发工作流 (11 个)

| Skill | 简介 |
|-------|------|
| `git-workflows` | Git 工作流 — 提交、推送、PR、分支清理 |
| `code-review-workflow` | 代码审查工作流 |
| `dev-workflows` | 开发工作流聚合 |
| `planning-with-files` | 多步骤任务规划 — Manus 式文件规划 |
| `executing-plans` | 执行已编写的实现计划 |
| `writing-plans` | 为多步骤任务编写实现计划 |
| `brainstorming` | 创意工作前的强制头脑风暴 |
| `dispatching-parallel-agents` | 并行子代理调度 |
| `using-git-worktrees` | Git Worktree 隔离开发 |
| `using-superpowers` | Skill 发现与使用引导 |
| `find-skills` | 帮助用户发现和安装 skills |

### 设计与前端 (7 个)

| Skill | 简介 |
|-------|------|
| `huashu-design` | 花叔 Design — 一体化 HTML 设计引擎（原型/动画/幻灯片/网站） |
| `imagegen-frontend-web` | Web 设计参考图生成 |
| `imagegen-frontend-mobile` | 移动 App 设计图生成 |
| `design-taste-frontend` | 前端设计品味参考 |
| `image-to-code-skill` | 设计稿转代码 |
| `image-analyzer` | 无视觉模型的图像理解代理 |
| `image-half-cut` | 批量图片上下对半裁切 |

### 文档处理 (7 个)

| Skill | 简介 |
|-------|------|
| `docx` | Word 文档创建/编辑/操作 |
| `pptx` | PowerPoint 创建与编辑 |
| `xlsx` | Excel 电子表格操作 |
| `pdf` | PDF 全面操作工具包 |
| `markitdown` | 文件转 Markdown（PDF/DOCX/PPTX/XLSX 等） |
| `markdown-mermaid-writing` | Markdown 与 Mermaid 图表写作 |
| `liteparse` | 本地文档和 PDF 解析 — 带空间文本和边界框 |

### MCP & Skill 构建 (7 个)

| Skill | 简介 |
|-------|------|
| `build-mcp-server` | 构建 MCP 服务器 |
| `build-mcp-app` | 构建带交互式 UI 的 MCP App |
| `build-mcpb` | 打包 MCP 服务器 |
| `skill-creator` | 创建/修改/评估 skills — 含测评和基准测试 |
| `tool-builder` | 交互式创建自定义 HTTP 工具 |
| `writing-skills` | Skills 编写指南 |
| `writing-rules` | Hookify 规则编写 |

### 幻灯片 & 演示 (3 个)

| Skill | 简介 |
|-------|------|
| `scientific-slides` | 科学演示幻灯片 |
| `guizang-ppt-skill` | PPT 生成 |
| `venue-templates` | LaTeX 模板汇集 — 期刊/会议投稿格式 |

### 科学写作 & 学术 (6 个)

| Skill | 简介 |
|-------|------|
| `scientific-writing` | 科学写作全流程 |
| `literature-review` | 文献综述工具包 |
| `scholar-evaluation` | 学术论文/学者评估 |
| `bgpt-paper-search` | 科学论文搜索 — 返回结构化实验数据 |
| `research-grants` | 研究基金申请书撰写（NSF/NIH/DOE/DARPA/NSTC） |
| `hypothesis-generation` | 科学假设自动生成 |
| `paperzilla` | Paperzilla 论文推荐和讨论 |

### 科学可视化 (2 个)

| Skill | 简介 |
|-------|------|
| `scientific-visualization` | 出版级科学图表元 skill |
| `scientific-schematics` | 出版级科学示意图 — AI 驱动 |

### GPU 与云计算 (3 个)

| Skill | 简介 |
|-------|------|
| `optimize-for-gpu` | GPU 加速 Python — CuPy/Numba/CuDF/CuML |
| `modal` | Modal 无服务器 GPU 云计算 |
| `dask` | 分布式计算 — 超内存 DataFrame/数组 |

### 生物信息学 & 计算生物学 (35 个)

| Skill | 简介 |
|-------|------|
| `biopython` | 分子生物学工具包 — 序列操作/文件解析/BLAST |
| `scanpy` | 单细胞 RNA-seq 标准分析流程 |
| `anndata` | 单细胞分析注释数据矩阵格式 |
| `scvi-tools` | 单细胞组学深度生成模型 |
| `scvelo` | RNA 速度分析 — 细胞状态转变推断 |
| `cellxgene-census` | CELLxGENE Census 查询（6100万+ 细胞） |
| `bulk-rnaseq` | 端到端 Bulk RNA-seq — FASTQ 到分析报告 |
| `pydeseq2` | 差异基因表达分析（Python DESeq2） |
| `pathway-enrichment` | 通路和基因集富集分析 |
| `arboreto` | 基因调控网络推断 — 可扩展集成方法 |
| `geniml` | 基因组区间数据机器学习 |
| `pysam` | 基因组文件工具包 — SAM/BAM/VCF/FASTQ 读写 |
| `polars-bio` | 高性能基因组区间操作 — Polars DataFrame 上 |
| `gtars` | 高性能基因组区间分析 — Rust + Python |
| `deeptools` | NGS 分析工具包 — BAM 到 bigWig、QC |
| `tiledbvcf` | 基因组变异数据高效存储 — TileDB |
| `bids` | 神经影像 BIDS 标准 |
| `neuropixels-analysis` | Neuropixels 神经记录分析 — 锋电位分类 |
| `neurokit2` | 综合生物信号处理 — 生理数据分析 |
| `phylogenetics` | 系统发育树构建与分析 — MAFFT/IQ-TREE |
| `etetoolkit` | 系统发育树工具包 — 树操作与进化事件 |
| `scikit-bio` | 生物数据工具包 — 序列/比对/多样性 |
| `polars` | 快速 DataFrame 库 — pandas 高性能替代 |
| `histolab` | 轻量 WSI 切片提取和预处理 |
| `pathml` | 全功能计算病理学 |
| `pydicom` | DICOM 医学影像处理 |
| `imaging-data-commons` | NCI 癌症影像数据查询下载 |
| `omero-integration` | 显微镜数据管理平台 |
| `gget` | 快速查询 20+ 生物信息学数据库 |
| `bioservices` | 统一 Python 接口 — 40+ 生物信息服务 |
| `matchms` | 代谢组学质谱相似度与化合物鉴定 |
| `pyopenms` | 完整质谱分析平台 — 蛋白质组学 |
| `primekg` | Precision Medicine 知识图谱查询 |
| `cobrapy` | 约束代谢建模 — FBA/FVA/基因敲除 |
| `flowio` | 流式细胞术 FCS 文件解析 |

### 药物发现 & 化学信息学 (10 个)

| Skill | 简介 |
|-------|------|
| `rdkit` | 化学信息学工具包 — SMILES/SDF/分子指纹 |
| `datamol` | RDKit 的 Pythonic 封装 — 简化接口 |
| `deepchem` | 分子机器学习 — 多 featurizer 和预建数据集 |
| `molfeat` | 分子特征化 — 100+ featurizer |
| `medchem` | 药物化学过滤 — Lipinski/PAINS/结构警报 |
| `diffdock` | 扩散模型分子对接 — 蛋白质-配体结合姿态预测 |
| `torchdrug` | PyTorch 原生分子/蛋白质 GNN |
| `pytdc` | Therapeutics Data Commons — AI 药物发现数据集 |
| `esm` | 蛋白质语言模型 — ESM3/ESM C 等 |
| `glycoengineering` | 蛋白质糖基化分析与工程 |

### 实验室自动化 & 云实验 (7 个)

| Skill | 简介 |
|-------|------|
| `opentrons-integration` | Opentrons OT-2/Flex 实验机器人协议 |
| `pylabrobot` | 跨厂商实验室自动化框架 |
| `protocolsio-integration` | protocols.io API 集成 |
| `benchling-integration` | Benchling R&D 平台集成 |
| `labarchive-integration` | 电子实验记录本 API |
| `ginkgo-cloud-lab` | Ginkgo Bioworks 云实验室 |
| `latchbio-integration` | Latch 生物信息学工作流平台 |

### 机器学习 & AI (11 个)

| Skill | 简介 |
|-------|------|
| `scikit-learn` | 经典机器学习全栈 |
| `pytorch-lightning` | PyTorch 深度学习框架 |
| `transformers` | HuggingFace 预训练 Transformer 模型 |
| `torch-geometric` | 图神经网络（PyTorch Geometric） |
| `hugging-science` | 科学领域的 AI/ML 工作 |
| `stable-baselines3` | 强化学习算法（PPO/SAC/DQN 等） |
| `pufferlib` | 高性能强化学习框架 |
| `shap` | 模型可解释性 — SHAP 值 |
| `pymc` | 贝叶斯建模 — MCMC/变分推断 |
| `umap-learn` | UMAP 降维 — 快速非线性流形学习 |
| `timesfm-forecasting` | TimesFM 时间序列预测 |

### 统计与可视化 (5 个)

| Skill | 简介 |
|-------|------|
| `statsmodels` | 统计模型 — 回归/时间序列/生存分析 |
| `scikit-survival` | 生存分析全栈 — Cox/Random Forest/GB |
| `seaborn` | 统计可视化 + pandas 集成 |
| `matplotlib` | 底层绑图库 — 完全定制 |
| `vaex` | 十亿级大数据处理与可视化 |

### 数学与物理 (8 个)

| Skill | 简介 |
|-------|------|
| `sympy` | 符号数学 — 微积分/代数/方程 |
| `math-olympiad` | 数学奥林匹克竞赛解题 |
| `qiskit` | IBM 量子计算框架 |
| `cirq` | Google 量子计算框架 |
| `pennylane` | 硬件无关量子 ML 框架 |
| `qutip` | 开放量子系统模拟 |
| `pymoo` | 多目标优化 — NSGA-II/III、MOEA/D |
| `networkx` | 复杂网络分析 |

### 地球科学与地理空间 (4 个)

| Skill | 简介 |
|-------|------|
| `geomaster` | 综合地理空间科学 — 遥感/GIS/空间分析 |
| `geopandas` | 地理空间矢量数据处理 |
| `fluidsim` | 计算流体力学 — Navier-Stokes/浅水波 |
| `aeon` | 时间序列机器学习 — 分类/回归/聚类 |

### 材料科学与模拟 (4 个)

| Skill | 简介 |
|-------|------|
| `pymatgen` | 材料科学工具包 — 晶体结构/相图/能带 |
| `molecular-dynamics` | 分子动力学模拟 — OpenMM + MDAnalysis |
| `simpy` | 离散事件仿真框架 |
| `pymatgen` | 材料科学 — CIF/POSCAR/相图/能带 |

### 临床与医疗 (4 个)

| Skill | 简介 |
|-------|------|
| `clinical-decision-support` | 临床决策支持文档生成 |
| `clinical-reports` | 临床报告撰写 — CARE 指南 |
| `treatment-plans` | 治疗方案生成 — LaTeX/PDF |
| `depmap` | Cancer Dependency Map — 基因依赖性/药物敏感性 |

### 生物与实验 (5 个)

| Skill | 简介 |
|-------|------|
| `adaptyv` | Adaptyv Bio Foundry — 蛋白质实验设计 |
| `rowan` | Rowan 云端分子建模平台 |
| `dhdna-profiler` | DH DNA 分析 |
| `pacsomatic` | nf-core/pacsomatic 肿瘤-正常分析 |
| `zarr-python` | 分块 N 维数组云端存储 |

### 平台与集成 (5 个)

| Skill | 简介 |
|-------|------|
| `nextflow` | Nextflow 数据管线构建与调试 |
| `dnanexus-integration` | DNAnexus 云端基因组学平台 |
| `pyzotero` | Zotero 文献管理 API |
| `usfiscaldata` | 美国财政数据 API 查询 |
| `matlab` | MATLAB/Octave 数值计算 |

### 其他工具 (8 个)

| Skill | 简介 |
|-------|------|
| `web-access` | 浏览器联网操作 — Chrome CDP 驱动 |
| `parallel-web` | 并行网页搜索/学术检索 |
| `automation` | Proma 定时任务系统 |
| `proma-coach` | Proma 使用顾问 — 优化工作流 |
| `memory-digest` | 会话记忆摘要 — 跨会话上下文注入 |
| `harness-memory` | 双模记忆系统 — BM25+向量混合检索 |
| `humanizer` | 文本人性化处理 |
| `elon-musk-perspective` | 马斯克思维模型 — 第一性原理/五步算法 |
| `consciousness-council` | 多视角意识讨论 |
| `hypogenic` | LLM 驱动自动假设生成与测试 |

### 已独立发布的 Skill

以下 skill 已有独立 GitHub 仓库，本仓库不再包含：

- [`metabase-doctor`](https://github.com/Starr/metabase-doctor) — Metabase 看板优化
- [`image-half-cut`](https://github.com/Starr/image-half-cut) — 批量图片裁切

## 目录结构

每个 skill 的标准结构：

```
skill-name/
├── SKILL.md          # 核心文件：skill 指令 + 触发规则
├── references/       # 参考文档（可选）
├── assets/           # 静态资源（可选）
├── scripts/          # 辅助脚本（可选）
└── evals/            # 测评用例（可选）
```

## 编写自己的 Skill

最小 skill 只需一个 `SKILL.md`：

```markdown
---
name: my-skill
description: 一句话描述 skill 用途和触发场景
---

# My Skill

## 何时触发
- 用户说 "xxx"
- 场景描述

## 工作流
1. 步骤一
2. 步骤二

## 前置依赖
- MCP: xxx
```

更多参考 [skill-creator](skills/skill-creator/) 和 [writing-skills](skills/writing-skills/)。

## License

MIT

## 贡献

欢迎提 Issue 和 PR。如果你有打磨好的 skill 想分享，请：
1. Fork 本仓库
2. 在 `skills/` 下添加你的 skill 目录
3. 更新 README 的对应分类表格
4. 提交 PR

---

**Author:** [Starr](https://github.com/Starr)
