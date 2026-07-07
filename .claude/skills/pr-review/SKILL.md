---
description: Reviews the current pull request with structured feedback across correctness, security, and code quality. Use when the user asks for a PR review, wants feedback on a pull request, or asks to review open changes.
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context

PR diff:
!`gh pr diff 2>/dev/null || echo "(no open PR on current branch)"`

PR description:
!`gh pr view 2>/dev/null || echo "(no open PR on current branch)"`

Changed files:
!`gh pr diff --name-only 2>/dev/null || echo ""`

## Review task

Provide a structured code review. Use these sections — omit any that don't apply:

### Summary
One paragraph on what the PR does and why.

### Correctness
Bugs, logic errors, edge cases that aren't handled, or incorrect behavior.

### Security
Injection risks, missing auth checks, data exposure, unsafe deserialization.

### Performance
Obvious inefficiencies: N+1 queries, unnecessary allocations, blocking calls.

### Code quality
Readability, naming, structure. Only flag things that meaningfully hurt maintainability.

### Suggestions
Concrete, actionable improvements with brief rationale.

### Verdict
**Approve** / **Request Changes** / **Needs Discussion** — one line explaining why.
