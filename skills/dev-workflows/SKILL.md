---
name: dev-workflows
description: >
  开发工作流三件套 — 实现前TDD（先写测试再写代码）、
  遇到bug时系统调试（先定位根因再修）、完成时验证（跑验证命令确认通过再声称完成）。
  三位一体的防御性开发流程。

  触发词 (中文): TDD、测试驱动开发、先写测试、debug、调试、
  先排查再修、验证完成、确认通过、run tests before commit。

  Trigger (EN): test-driven development, TDD, write tests first,
  debug, systematic debugging, verify before completion,
  run verification, evidence before assertion.
user-invocable: true
---

# Dev Workflows

## TDD (Test-Driven Development)
实现任何功能或修bug前：先写失败测试 → 确认测试失败 → 写最小实现 → 确认测试通过 → 重构。

## Systematic Debugging
遇到任何bug/测试失败/异常行为时：先定位根因 → 提出假设 → 验证假设 → 修复最小范围。

## Verification Before Completion
声称完成/修复/通过前：跑验证命令 → 确认输出 → 再声称。证据先于断言。
