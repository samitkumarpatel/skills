---
name: spring-testing
description: Create, update, or review tests for Spring and Spring Boot applications, including unit tests, controller tests, HTTP endpoint integration tests, outbound API stubs, and infrastructure integration tests. Apply the user's RestTestClient, MockMvc, WireMock, and Testcontainers preferences.
---

# Spring testing

Follow the official [Spring Framework testing reference](https://docs.spring.io/spring-framework/reference/testing.html)
for general Spring testing patterns and the
[Spring Boot testing reference](https://docs.spring.io/spring-boot/reference/testing/index.html)
for Boot-specific test support. Inspect the project's Java, Framework, Boot,
and testing-library versions and use matching documentation, imports, and
dependencies. Do not silently upgrade the application to adopt a test API.

Load only references relevant to the requested test:

| Test concern | Guidance |
| --- | --- |
| Unit tests and business logic | [Unit tests](references/unit.md) |
| API endpoint integration, traditional controllers, functional routes | [HTTP tests](references/http.md) |
| Spring Boot context, slices, and test configuration | [Boot tests](references/boot.md) |
| Mocking an external HTTP API | [WireMock](references/wiremock.md) |
| Real databases, brokers, and deeper integration | [Testcontainers](references/testcontainers.md) |

These approaches can be combined: an endpoint integration test can use
RestTestClient, WireMock for external APIs, and Testcontainers for its database.
Choose dependencies according to the boundary being verified rather than
starting every test with a full application context.

Test observable behavior and relevant failure cases. Keep fixtures isolated,
avoid fixed ports and timing-based waits, and run the project's appropriate test
commands. Report unavailable infrastructure or skipped checks explicitly;
do not replace an intended integration test with mocks merely to obtain a pass.
