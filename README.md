# Coding-agent skills

Personal coding conventions packaged as reusable skills. This repository is the
source for skills; registration with a particular coding agent is separate.

## Current skills

| Skill | Entrypoint | Status |
| --- | --- | --- |
| Java best practices | [java-best-practices/SKILL.md](java-best-practices/SKILL.md) | Records first, modern Java features, and Project Loom concurrency |
| Spring testing | [spring-testing/SKILL.md](spring-testing/SKILL.md) | Unit, Boot, and HTTP tests; RestTestClient, MockMvc, WireMock, and Testcontainers |
| Spring Boot | [springboot/SKILL.md](springboot/SKILL.md) | Initializr-first setup; HTTP routing and tests; business services, repositories, and HTTP Service Clients |

## Layout

```text
skills/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── java-best-practices/
│   └── SKILL.md
├── spring-testing/
│   ├── SKILL.md
│   └── references/
│       ├── unit.md
│       ├── http.md
│       ├── boot.md
│       ├── wiremock.md
│       └── testcontainers.md
└── springboot/
    ├── SKILL.md
    └── references/
        ├── conventions.md
        ├── services.md
        └── web.md
```

Each skill has its own directory and `SKILL.md`. Add references, executable
helpers, or starter assets when there is actual content to maintain.

## Building the Spring Boot skill

Start by describing your usual project starting point. Then share your preferred
controller, service, and repository patterns, followed by other conventions.
Existing code examples are useful when available. Preferences are recorded in
[the convention reference](springboot/references/conventions.md) as provided;
undecided topics do not impose defaults.

## Using a skill

For an agent that can read local files, ask it to read `springboot/SKILL.md` by
its full path and apply it to the target project. For automatic discovery, use
your agent's skill registration mechanism with the entire `springboot/` directory
so relative references remain available. Agent registration has not been set up.
