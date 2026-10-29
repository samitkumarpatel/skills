# Services and outbound API calls

## Confirmed service responsibilities

Put business logic in the service layer for use by controllers and functional
HTTP handlers. Services use the repository package for data-related queries
and persistence operations. Keep database queries in repositories rather than
embedding them in service or controller code.

The intended flow is:

```text
Controller / HTTP handler → Service → Repository → Data store
                                  → HTTP Service Client → External API
```

Services coordinate the business operation; repositories handle data access,
and HTTP clients describe outbound API interactions. Do not route database
queries directly from controllers around the service layer.

Service interfaces, naming conventions, transaction boundaries, and error
contracts have not yet been specified. Follow the target project's existing
patterns for those choices rather than introducing new personal conventions.

## Preferred outbound API approach

Prefer Spring HTTP Service Clients when a business operation consumes an
external API. Treat this as the user's usual approach, not a mandate to replace
existing integrations during unrelated work.

Use the user's reference,
[HTTP Service Client Enhancements](https://spring.io/blog/2025/09/23/http-service-client-enhancements/),
as the starting point. Define HTTP interfaces with `@HttpExchange` and relevant
method annotations such as `@GetExchange` or `@PostExchange`; inject the
configured client into the service that needs it.

Check the project's Spring Framework and Boot versions before choosing client
registration and configuration. The article distinguishes the interface/proxy
support introduced in Framework 6 from Framework 7's registry, groups, and
`@ImportHttpServices`, plus Boot 4's group configuration support. Use only APIs
and properties supported by the target version; consult its official reference
for exact setup. For older compatible projects, use explicit proxy/bean
configuration when newer registration is unavailable, without upgrading the
application merely to follow the article.

Select the underlying transport to match the application's execution model.
Keep client setup outside business methods and reuse configured client beans.
Do not prescribe authentication, retries, resilience libraries, or client
package names until the task or the user's conventions require them.

If dependencies are needed, follow the Initializr-first workflow in
[conventions.md](conventions.md).
