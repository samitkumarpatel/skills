---
name: springboot
description: Implement or review Spring Boot code using the user's conventions. Use for new Spring projects, Spring ecosystem dependency discovery and compatibility checks, controllers, services, repositories, and related application changes.
---

# Spring Boot conventions

Read [references/conventions.md](references/conventions.md) before implementing
or reviewing Spring Boot code. Apply confirmed preferences relevant to the task.
For new projects and Spring ecosystem dependency discovery or compatibility
checks, follow its Spring Initializr workflow first. Other conventions will be
recorded as the user provides them.

For HTTP routes, controllers, and their tests, read
[references/web.md](references/web.md). It records the functional-routing
preference, the transition to annotated controllers, and documentation sources.

For business logic, service-layer changes, or outbound API calls, read
[references/services.md](references/services.md) for service/repository
boundaries and the HTTP Service Client preference.

Inspect the target project's instructions, build configuration, and nearby code
before choosing a pattern. Preserve its established versions and conventions
unless the user asks to change them. If a confirmed preference conflicts with
the project, identify the conflict and resolve it within the requested scope;
do not silently migrate unrelated code.

For an unspecified topic, follow the target project's established pattern. When
starting a new project and an unresolved choice materially affects the requested
work, ask a focused question. Treat minor implementation choices as local
decisions, not new personal conventions.

When the user supplies a convention, update the reference with its scope and a
small example if useful. Separate confirmed requirements from optional
preferences. Do not infer a universal rule from an isolated code example.

Validate application changes with the target project's relevant build and checks.
Do not generate an application or introduce dependencies merely because this
skill was loaded.
