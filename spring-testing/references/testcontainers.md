# Deeper integration with Testcontainers

Prefer Testcontainers for deeper integration tests that require real backend
services such as a database, cache, or broker. Follow the official
[Spring Boot Testcontainers reference](https://docs.spring.io/spring-boot/reference/testing/testcontainers.html)
matching the project's Boot version.

Choose the relevant backend container and an explicit image version compatible
with the application's target environment. Wire connections using Boot service
connections (`@ServiceConnection`) where supported; otherwise use the documented
dynamic-property configuration. Use mapped addresses rather than fixed ports.

Match container lifetime to the test application context. Prefer Boot-managed
container beans or supported imported declarations when context caching could
outlive a JUnit-managed container. Use readiness checks instead of arbitrary
sleeps, isolate test data, and verify real queries, migrations, or messaging
behavior relevant to the change.

Combine with HTTP tests and WireMock when the scenario crosses those boundaries.
Do not require containers for pure unit tests or controller slices with no real
infrastructure dependency. If the container runtime is unavailable, report the
blocked integration check rather than silently skipping or substituting mocks.
