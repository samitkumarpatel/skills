---
description: Summarizes uncommitted changes and flags anything risky. Use when the user asks what changed, wants a commit message drafted, asks to review their diff, or wants to understand what they've modified since the last commit.
---

## Uncommitted changes
!`git diff HEAD`

## Working tree status
!`git status --short`

## Instructions

Summarize the changes above:

1. Give 2–3 bullet points describing what was changed and why (infer intent from the diff)
2. Flag any risks you notice:
   - Missing error handling
   - Hardcoded credentials or secrets
   - Tests that need updating
   - Potential breaking changes to public APIs
   - Large deletions or moved logic
3. Suggest a one-line conventional commit message summarizing the work
4. If the diff is empty, say there are no uncommitted changes
