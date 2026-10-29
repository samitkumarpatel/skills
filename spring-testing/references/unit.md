# Unit tests

Follow the unit-testing section of the
[Spring Framework testing reference](https://docs.spring.io/spring-framework/reference/testing.html).

For isolated business logic, instantiate the class with controlled collaborators
without starting Spring. Use the project's existing test framework and assertion
style. Cover meaningful outcomes, invariants, and error paths. Mock or fake
collaborators at the unit boundary when useful; avoid asserting incidental
implementation steps.

An HTTP client mock can isolate a service unit test. When testing the outbound
HTTP integration itself, use [WireMock](wiremock.md) to exercise the real client.
Use Spring context or [Boot test support](boot.md) when framework wiring or
configuration is part of the behavior under test.
