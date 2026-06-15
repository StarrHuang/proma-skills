---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans — creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**In Proma:** Use the built-in `EnterWorktree` / `ExitWorktree` tools which handle worktree creation and cleanup automatically. This skill provides the methodology for directory selection, safety verification, and project setup around those tools.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```bash
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check CLAUDE.md / workspace config

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

**If preference specified:** Use it without asking.

### 3. Ask User

If no directory exists and no config preference:

> No worktree directory found. Where should I create worktrees?
> 1. .worktrees/ (project-local, hidden)
> 2. ~/.config/superpowers/worktrees/<project-name>/ (global location)

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**MUST verify directory is ignored before creating worktree:**

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**If NOT ignored:** Add appropriate line to .gitignore and commit the change.

### For Global Directory

No .gitignore verification needed — outside project entirely.

## Creation (Proma)

Use Proma's built-in `EnterWorktree` tool:

```
EnterWorktree(name: "<branch-name>")
```

This creates an isolated git worktree in `.claude/worktrees/` with a new branch, then switches the session into it.

### Project Setup After Creation

Auto-detect and run appropriate setup:

```bash
[ -f package.json ] && npm install      # Node.js
[ -f requirements.txt ] && pip install -r requirements.txt  # Python
[ -f pyproject.toml ] && poetry install
[ -f go.mod ] && go mod download        # Go
[ -f Cargo.toml ] && cargo build        # Rust
```

### Verify Clean Baseline

Run tests to ensure worktree starts clean. If tests fail: report failures, ask whether to proceed.

## Cleanup (Proma)

Use Proma's built-in `ExitWorktree` tool:

```
ExitWorktree(action: "keep")    # Leave worktree on disk, return to original dir
ExitWorktree(action: "remove")  # Delete worktree and branch
```

For `remove`, if the worktree has uncommitted changes, set `discard_changes: true`.

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Tests fail during baseline | Report failures + ask |
| No project files | Skip dependency install |

## Common Mistakes

- **Skipping ignore verification** — worktree contents get tracked, pollute git status. Fix: always `git check-ignore` first
- **Proceeding with failing tests** — can't distinguish new bugs from pre-existing issues. Fix: report failures, get permission

## Integration

**Called by:**
- **brainstorming** — REQUIRED when design is approved
- **subagent-driven-development** — REQUIRED before executing tasks
- **executing-plans** — REQUIRED before executing tasks
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** — REQUIRED for cleanup after work complete
