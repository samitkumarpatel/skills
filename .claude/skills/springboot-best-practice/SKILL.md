---
description: Spring Boot best practices for project structure, layering, exception handling, configuration, validation, logging, and HTTP service clients. Applies automatically when working on Spring Boot Java projects, writing controllers, services, repositories, configuration classes, or @HttpExchange HTTP client interfaces.
user-invocable: false
paths: "**/*.java,**/pom.xml,**/application.yml,**/application.properties"
---

!`python3 -c "import json,urllib.request; req=urllib.request.Request('https://start.spring.io',headers={'Accept':'application/json'}); d=json.load(urllib.request.urlopen(req,timeout=5)); print('start.spring.io current defaults — Spring Boot: '+d['bootVersion']['default']+', Java: '+d['javaVersion']['default'])" 2>/dev/null || echo "start.spring.io unavailable — use latest stable Spring Boot and latest Java LTS"`

## Getting started

Always use the **latest stable Spring Boot** release and the **latest Java LTS** version (see injected defaults above). Generate new projects from [start.spring.io](https://start.spring.io/) — never hand-craft the build file or hardcode dependency versions; let Spring's managed BOM handle them.

### Essential dependencies

Artifact IDs reflect **Spring Boot 4.0** names from the [Spring Boot 4.0 Migration Guide — Starters](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide#starters). Run `python3 .claude/skills/springboot-best-practice/scripts/search-deps.py [keyword]` to search all available starters from start.spring.io, or `--versions` to list Boot and Java version options.

| Starter | Artifact ID | Purpose |
|---|---|---|
| Spring MVC | `spring-boot-starter-webmvc` | REST controllers, HTTP layer |
| Spring Data JPA | `spring-boot-starter-data-jpa` | Database access via repositories |
| Validation | `spring-boot-starter-validation` | Jakarta Bean Validation |
| Spring Security | `spring-boot-starter-security` | Authentication and authorization |
| OAuth2 Resource Server | `spring-boot-starter-security-oauth2-resource-server` | JWT / OAuth2 resource server |
| OAuth2 Client | `spring-boot-starter-security-oauth2-client` | OAuth2 / OIDC login flows |
| Flyway | `spring-boot-starter-flyway` | Database migrations |
| Actuator | `spring-boot-starter-actuator` | Health, metrics, Prometheus |
| Lombok | `lombok` (annotation processor, not a starter) | `@Slf4j`, `@RequiredArgsConstructor`, etc. |
| Testcontainers | `spring-boot-testcontainers` | Real containers in integration tests |

Every starter above has a corresponding test variant — append `-test` (e.g. `spring-boot-starter-webmvc-test`, `spring-boot-starter-data-jpa-test`, `spring-boot-starter-security-test`).

## Project structure

```
src/main/java/com/example/
├── controller/     # @RestController — HTTP boundary only
├── service/        # @Service — all business logic
├── repository/     # @Repository — data access only
├── model/          # @Entity / domain objects
├── dto/            # Request/response POJOs (records preferred)
├── exception/      # Custom exceptions + @ControllerAdvice
└── config/         # @Configuration classes
```

## Dependency injection

Always use **constructor injection**. Never `@Autowired` on fields.

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentService  paymentService;
}
```

## Layering rules

- Controllers are thin: validate input, call one service method, return response
- Services own all business logic and transactions
- Repositories are interface-only (Spring Data); no custom SQL in service layer
- Never expose `@Entity` classes in API responses — always map to DTOs
- Cross-service calls go service → service, never repository → repository


## Supporting references

- Exception handling (ProblemDetail, @ControllerAdvice, custom exceptions): [exception-handling.md](exception-handling.md)
- Validation (Bean Validation, Jakarta constraints, custom validators): [validation.md](validation.md)
- Logging (SLF4J, @Slf4j, levels, structured params, JSON output): [logging.md](logging.md)
- Configuration (profiles, @ConfigurationProperties, secrets, Actuator): [configuration.md](configuration.md)
- Security (JWT, OAuth2 resource server, method security, CORS): [security.md](security.md)
- Testing (JUnit 5, MockMvc, Testcontainers, test slices, Modulith): [testing.md](testing.md)
- HTTP service clients (@HttpExchange, registry, Boot 4 properties): [http-service-client.md](http-service-client.md)
- Spring Modulith (modular architecture, events, verification, documentation): [spring-modulith.md](spring-modulith.md)
- Spring MVC (DispatcherServlet, controllers, routing, binding, CORS, interceptors, MockMvc): [mvc.md](mvc.md)
- Spring Data JDBC (aggregate design, mapping annotations, repositories, @Query, custom converters, auditing, callbacks): [spring-data-jdbc.md](spring-data-jdbc.md)
