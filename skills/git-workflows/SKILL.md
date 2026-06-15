---
name: git-workflows
description: >
  Git 工作流快捷操作 — 提交、推送、创建PR、清理远程分支、
  完成开发分支后结构化决策（merge/PR/cleanup三种选项）。

  触发词: commit、push、PR、清理分支、merge、完成开发分支、合并代码。
---

# Git 工作流

## 工作流 1: 创建提交

基于当前变更创建一个 git commit。

### 步骤

1. 并行执行以下命令收集上下文：
   - `git status`
   - `git diff HEAD`
   - `git branch --show-current`
   - `git log --oneline -10`

2. 分析变更内容，遵循仓库的 commit 风格撰写 commit message

3. 执行提交：
   ```bash
   git add <specific-files>
   git commit -m "$(cat <<'EOF'
   <commit message>

   Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
   EOF
   )"
   ```

---

## 工作流 2: 提交 + 推送 + 创建 PR

基于当前变更创建提交、推送、并创建 PR。

### 步骤

1. 并行执行：
   - `git status`
   - `git diff HEAD`
   - `git branch --show-current`

2. 如果在 main 分支上，先创建新分支：
   ```bash
   git checkout -b <descriptive-branch-name>
   ```

3. Stage 变更并创建提交（同工作流 1）

4. 推送到远程：
   ```bash
   git push -u origin HEAD
   ```

5. 创建 PR：
   ```bash
   gh pr create --title "<pr title>" --body "$(cat <<'EOF'
   ## Summary
   <1-3 bullet points>

   ## Test plan
   [Bulleted checklist]

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

---

## 工作流 3: 清理 Gone 分支

清理远程已删除但本地还存在的分支（标记为 `[gone]`）。

### 步骤

1. 列出分支状态：
   ```bash
   git branch -v
   ```

2. 列出 worktree：
   ```bash
   git worktree list
   ```

3. 删除所有 `[gone]` 分支及其关联 worktree：
   ```bash
   git branch -v | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
     echo "Processing branch: $branch"
     worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
     if [ ! -z "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi
     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

4. 如果没有 `[gone]` 分支，报告无需清理。

---

## 注意事项

- 提交前不要使用 `git add -A` 或 `git add .`，应精确选择要 stage 的文件
- 不要跳过 git hooks（`--no-verify`, `--no-gpg-sign`）
- 不要 force push 到 main/master
- 如果 pre-commit hook 失败，修复问题后创建新的 commit，不要 amend
