---
description: Creates a new skill in this repository. Use when the user wants to add a new custom skill, create a reusable command, or package up a repeated workflow.
disable-model-invocation: true
argument-hint: "[skill-name]"
---

## Instructions

Create a new Claude Code skill named `$ARGUMENTS` in this repository.

### Steps

1. Create the directory `.claude/skills/$ARGUMENTS/`
2. Write `.claude/skills/$ARGUMENTS/SKILL.md` with:
   - YAML frontmatter with `description` (required) and any relevant optional fields
   - Clear, concise instructions — assume Claude is smart, only add what it doesn't already know
   - `disable-model-invocation: true` if this skill has side effects or should only run on explicit request
   - `context: fork` + `agent: Explore` if it benefits from isolation and read-only exploration
3. Add supporting files (e.g. `reference.md`, `scripts/`) only if the skill body would exceed ~500 lines otherwise
4. Refer to [SKILL.md best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) when in doubt

### Key frontmatter fields

| Field | When to use |
|---|---|
| `description` | Always — drives automatic discovery |
| `disable-model-invocation: true` | Side-effect skills (deploy, commit, send) |
| `allowed-tools: Bash(...)` | Pre-approve specific commands |
| `context: fork` | Skills that benefit from isolated context |
| `argument-hint: [...]` | Skills that accept arguments |
| `when_to_use` | Extra trigger phrases beyond `description` |

### After creating

Briefly explain what the new skill does and how to invoke it (`/skill-name` or automatic).

If no name was given in `$ARGUMENTS`, ask the user what skill they want to create before proceeding.
