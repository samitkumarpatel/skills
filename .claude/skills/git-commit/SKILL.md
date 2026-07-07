---
description: Stage and commit the current changes with a conventional commit message. Use when the user wants to commit their work, asks to create a commit, or wants staged changes committed.
disable-model-invocation: true
allowed-tools: Bash(git *)
argument-hint: "[message hint]"
---

## Current state
!`git status --short`

## Staged diff
!`git diff --cached`

## Unstaged diff
!`git diff`

## Instructions

Create a git commit for the changes above:

1. Review all staged and unstaged changes shown
2. If nothing is staged, stage relevant files — skip build artifacts, `node_modules`, `.env*`, and generated files
3. Write a commit message following [Conventional Commits](https://www.conventionalcommits.org):
   - Format: `type(scope): description`
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   - Subject line under 72 characters, imperative mood ("add" not "adds")
   - Add a blank line + body paragraph if the change is non-trivial
4. Commit using a heredoc for multi-line messages:
   ```bash
   git commit -m "$(cat <<'EOF'
   type(scope): subject

   Optional body here.
   EOF
   )"
   ```
5. Show the resulting commit hash

If `$ARGUMENTS` was provided, treat it as a hint for the commit message subject.
