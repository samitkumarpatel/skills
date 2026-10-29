# Spring Boot test support

Use the [Spring Boot testing reference](https://docs.spring.io/spring-boot/reference/testing/index.html)
matching the project's Boot release for starters, focused test modules,
auto-configuration, slices, context loading, and test properties. Verify exact
annotation packages and client configuration against that release.

- Use a focused test slice when testing a specific Boot-supported layer.
- Use `@SpringBootTest` when application-wide wiring is part of the test.
- For live HTTP endpoint integration, use a running test server, typically
  `@SpringBootTest(webEnvironment = RANDOM_PORT)`, and configure RestTestClient
  with the allocated address using the version-supported setup.
- Keep test properties and supporting beans scoped to tests. Load the advice,
  security, migrations, or serialization configuration needed by the assertion.

Use Boot-managed dependency versions where available. Do not copy dependencies
or annotation imports from a different major version. Verify whether required
test support needs an additional module in the project's Boot version.
