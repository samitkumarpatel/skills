# Maintaining this skill repository

This repository contains reusable coding-agent skills, not an application.
Each top-level skill directory contains a `SKILL.md` entrypoint with YAML
`name` and `description` fields. Keep skills independent of a particular agent
where practical.

When creating or updating a skill:

- Capture the user's stated conventions; do not invent their preferences.
- Distinguish confirmed conventions from open decisions. Open decisions are
  discussion prompts, not instructions for generated code.
- Keep entrypoints concise. Put detailed conventions in linked references,
  loaded only when relevant.
- Add scripts or templates only when a concrete workflow requires them.
- Replace superseded guidance instead of appending contradictory rules.
- Check frontmatter, relative links, and consistency after edits.

Do not restore removed skills or install into other repositories unless requested.
