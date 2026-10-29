# External API tests with WireMock

Prefer WireMock when mocking an HTTP API. Follow the official
[WireMock Spring Boot integration](https://wiremock.org/docs/spring-boot/)
for compatible dependencies and configuration.

Use the integration's `@EnableWireMock` setup when appropriate, with dynamic
ports. Route the application's actual HTTP client's base URL to the WireMock
instance via test configuration; stubbing a server that the client never calls
does not verify the integration.

Stub the request method, path, and relevant request data, then assert application
behavior and verify important outbound requests. Cover error responses or
timeouts when those are part of the contract. Isolate mappings and request state
between tests, especially for shared contexts. Multiple external APIs can use
separate instances or suitable separate mappings.

Keep dependencies in test scope/configuration. Verify library and Boot
compatibility rather than copying the documentation's latest version number.
