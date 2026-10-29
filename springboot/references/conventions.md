# Personal Spring Boot conventions

## Confirmed context

This is the first skill in the user's coding-agent skill collection. The user
will describe their project starting point and preferences for controllers,
services, repositories, and other concerns incrementally.

The dependency discovery workflow below,
[HTTP routing and testing conventions](web.md), and
[service and outbound API conventions](services.md) are confirmed. Project
versions and persistence choices are still open.

## Project setup and Spring dependency discovery

Start with [Spring Initializr](https://start.spring.io/) when creating a new
project or looking for a Spring-related dependency. This includes Spring Boot,
Spring Security, Spring Data, Spring AI, and other Spring ecosystem projects.

- Check Initializr's current dependency catalog first to find the relevant
  dependency and its compatibility with the intended Spring Boot version.
- For an existing project, inspect its Spring Boot version before checking
  compatibility. Do not upgrade the project just to use a dependency.
- Use the selected Boot version and Initializr's generated build configuration
  to guide dependency declarations and managed versions. Do not guess artifact
  coordinates or pin versions from memory.
- For a new project, use Initializr as the starting point for project generation,
  with the user's chosen project settings and compatible dependencies.
- If Initializr does not list the dependency or establish the needed
  compatibility, consult that Spring project's official documentation next.
  Absence from Initializr alone does not prove incompatibility. If Initializr
  cannot be accessed, report that limitation and use official Spring sources.

Check the live source when performing these tasks rather than embedding a
version or compatibility matrix in this skill. Include the source and relevant
compatibility findings when explaining a dependency choice.

## Topics to capture

These are prompts for future discussion, not coding requirements. Only ask about
topics relevant to the user's current request.

| Topic | Useful details to record when provided |
| --- | --- |
| Project starting point | Java and Spring Boot versions, build tool, starter project, dependencies, configuration, package organization |
| Further controller details | Project-specific request and response types, naming, and error contracts beyond the confirmed web conventions |
| Further service details | Naming, interfaces, dependency injection, transaction boundaries, business errors |
| Repositories | Persistence technology, entity conventions, queries, pagination, migrations |
| Other conventions | Security, logging, configuration, documentation, deployment |

As preferences arrive, replace the relevant open topic with confirmed guidance.
For substantial topics, move details into a focused reference and link it from
`SKILL.md`; keep this file as the index and shared context.
