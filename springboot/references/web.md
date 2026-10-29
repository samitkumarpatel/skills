# HTTP routing, controllers, and tests

## Confirmed preference

Use functional routing with `RouterFunction` for small, simple HTTP routing needs.
When the requirements exceed what `RouterFunction` can support for the task,
use an annotated controller class with `@GetMapping`, `@PostMapping`, and the
other applicable mapping annotations. Explain the concrete requirement that
motivates this choice. Do not impose an arbitrary endpoint-count threshold or
assume that validation, filters, or error handling alone require a controller.

Respect the target project's existing approach when making scoped changes;
this preference does not request a rewrite of existing endpoints.

## Documentation-driven implementation

Use the official [Spring Framework web reference](https://docs.spring.io/spring-framework/reference/web.html)
as the starting point for implementation and related tests. Select documentation
matching the project's Spring Framework version rather than assuming the latest
reference applies.

The supplied reference covers the Servlet stack. Inspect the project before
choosing imports or test infrastructure: functional routing does not imply
WebFlux. Use the corresponding reactive documentation only for a WebFlux project.

- For Servlet functional routes, follow
  [WebMvc.fn functional endpoints](https://docs.spring.io/spring-framework/reference/web/webmvc-functional.html)
  for routing, predicates, handlers, request/response handling, and filters.
- For controller classes, follow
  [annotated controllers](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html)
  and its relevant subsections for mappings, method arguments, request bodies,
  validation, return values, HTTP responses, and exception handling. Use
  `@RestController` for response-body APIs and `@Controller` when view handling
  is needed. Include only features required by the endpoint contract.
- For an existing reactive project, use
  [WebFlux functional endpoints](https://docs.spring.io/spring-framework/reference/web/webflux-functional.html)
  or the corresponding annotated-controller documentation. Do not mix Servlet
  and reactive `RouterFunction`, `ServerRequest`, or `ServerResponse` types.

## Tests around the HTTP contract

Follow the official testing documentation for the selected stack and project
version. Exercise requests through the routing/controller infrastructure so
tests verify mappings and serialization as well as handler behavior.

- For MVC annotated controllers, consult
  [MockMvc](https://docs.spring.io/spring-framework/reference/testing/mockmvc.html)
  and select a supported setup that includes the relevant configuration.
- For API endpoint integration tests, prefer
  [RestTestClient](https://docs.spring.io/spring-framework/reference/testing/resttestclient.html)
  against the running test application. Use its MVC router binding for focused
  functional-route tests where supported by the project's version.
- For Boot-specific context, slices, and test configuration, follow the
  [Boot testing reference](https://docs.spring.io/spring-boot/reference/testing/index.html).
  Use [WireMock](https://wiremock.org/docs/spring-boot/) for external HTTP API
  stubs and [Testcontainers](https://docs.spring.io/spring-boot/reference/testing/testcontainers.html)
  for deeper integration requiring real backends.
- For reactive functional routes, consult
  [WebTestClient](https://docs.spring.io/spring-framework/reference/testing/webtestclient.html),
  including its router-binding setup.
- Do not assume `WebTestClient.bindToRouterFunction` supports Servlet routes.
  Check the project's version-specific documentation for supported MVC
  functional-route testing; use an HTTP test against a running application
  when the needed mock binding is unavailable.

Cover successful requests and applicable contract failures: invalid input,
missing resources, method/path matching, status codes, headers, and response
bodies. Include security behavior when the endpoint has security requirements.
Choose cases relevant to the change; these are not a mandatory checklist for
every endpoint. When configuration affects behavior, include it in the test
rather than relying solely on a direct handler-method unit test.
