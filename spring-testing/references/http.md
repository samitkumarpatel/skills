# HTTP endpoint and controller tests

## API endpoint integration

Prefer [RestTestClient](https://docs.spring.io/spring-framework/reference/testing/resttestclient.html)
for API endpoint integration tests. For a complete HTTP boundary, bind to the
running test application using its allocated port. In a Boot application, follow
[Boot test support](boot.md) for starting the server and configuring the client.
Do not present a mock-bound client test as a live-server integration test.

Verify status, relevant headers, serialized bodies, and applicable validation,
not-found, and security behavior. Use [WireMock](wiremock.md) for external APIs
and [Testcontainers](testcontainers.md) for real backend dependencies as needed.

## Traditional annotated controllers

Prefer [MockMvc](https://docs.spring.io/spring-framework/reference/testing/mockmvc.html)
for focused MVC controller tests. Select standalone setup or a web context/slice
according to the behavior being tested. Include required advice, converters,
validation, and security configuration when they affect the contract. Mock
service collaborators when those are outside the controller test boundary.

## Functional routes and compatibility

For MVC functional-route tests, use RestTestClient's router binding when supported
by the project's Framework version, or test through the running server.
RestTestClient is a newer API: verify availability and setup in the target
version. If unavailable, explain the limitation and use the project's supported
HTTP test client without upgrading the application implicitly.

For reactive-specific tests, consult the official
[WebTestClient reference](https://docs.spring.io/spring-framework/reference/testing/webtestclient.html).
Its direct router binding uses reactive routes; do not pass Servlet routes to it.
Keep the RestTestClient preference for live API integration tests where supported.
