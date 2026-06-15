# sif-keyword-scout

Amazon Sif 关键词三表处理 skill：接入「关键词调研 / 反查流量词 / 查广告词」三张导出表，生成关键词分层、竞品弱点、广告缺口和 PD 主攻词单，并由 Agent 写入策略解读后输出 Excel + Word 报告。

## 安装

将 `sif-keyword-scout`、`sif-keyword-tracker`、`web-access` 三个目录放在同一个 skills 根目录下，并把 `.sif-config.example.json` 放在它们的同级目录。首次运行时脚本会复制为本地 `.sif-config.json` 并询问报告输出目录。

```bash
mkdir -p ~/.codex/skills
cp -R sif-keyword-scout sif-keyword-tracker web-access ~/.codex/skills/
cp .sif-config.example.json ~/.codex/skills/
python3 -m pip install pandas openpyxl matplotlib python-docx numpy
```

## 使用

对 Agent 说：

```text
运行 sif 关键词 skill，ASIN B08PNQCKF7
```

Agent 会先确认 ASIN、产品阶段、标品/非标品、精确类目和数据来源，然后在三个暂停点让用户确认门槛、主攻词方向和历史投放建议。完整执行细则见 `SKILL.md` 和 `references/first-time-setup.md`。
