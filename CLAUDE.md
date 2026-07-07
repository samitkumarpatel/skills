# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository stores Claude Code agent skills — reusable, filesystem-based instructions that extend Claude's capabilities. Skills live in `.claude/skills/<name>/SKILL.md`.

## Skill structure

Every skill is a directory under `.claude/skills/` with a `SKILL.md` file:

```
.claude/skills/<skill-name>/
├── SKILL.md          # Required: frontmatter + instructions
├── reference.md      # Optional: detailed docs loaded on demand
└── scripts/          # Optional: executable scripts
    └── helper.py
```

**SKILL.md frontmatter** (YAML between `---` markers):

| Field | Required | Notes |
|---|---|---|
| `description` | Yes | What the skill does + when to use it. Third person. Max 1024 chars. |
| `name` | No | Display label; defaults to directory name |
| `disable-model-invocation` | No | `true` for side-effect skills (commit, deploy) |
| `allowed-tools` | No | Pre-approve tools, e.g. `Bash(git *)` |
| `context` | No | `fork` to run in an isolated subagent |
| `agent` | No | Subagent type when `context: fork`: `Explore`, `Plan`, `general-purpose` |
| `argument-hint` | No | Shown in autocomplete, e.g. `[issue-number]` |

**Dynamic context injection** — run shell commands before Claude sees the skill:
```
!`git diff HEAD`
```

**Arguments** — available via `$ARGUMENTS`, `$0`, `$1`, etc.

## Skills in this repo

| Skill | Invoke | Purpose |
|---|---|---|
| `git-commit` | `/git-commit [hint]` | Stage and commit with a conventional commit message |
| `summarize-changes` | auto or `/summarize-changes` | Summarize uncommitted diff + flag risks |
| `pr-review` | auto or `/pr-review` | Structured PR review in a forked Explore agent |
| `create-skill` | `/create-skill [name]` | Scaffold a new skill in this repo |
| `calculator` | auto or `/calculator [expr]` | Evaluate math expressions and unit conversions via Python |
| `springboot-best-practice` | auto (Java/Spring files) | Background reference for structure, layering, exceptions, testing, security, config |

## Adding a new skill

Run `/create-skill <skill-name>` or manually:
1. `mkdir .claude/skills/<name>`
2. Write `SKILL.md` with frontmatter + instructions
3. Keep the body under 500 lines; move detail to supporting files

## References

- [Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Code skills docs](https://code.claude.com/docs/en/skills)
- [Best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
