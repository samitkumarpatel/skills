---
description: Spring Boot best practices for project structure, layering, exception handling, configuration, validation, logging, and HTTP service clients. Applies automatically when working on Spring Boot Java projects, writing controllers, services, repositories, configuration classes, or @HttpExchange HTTP client interfaces.
user-invocable: false
paths: "**/*.java,**/pom.xml,**/build.gradle,**/build.gradle.kts,**/application.yml,**/application.properties"
---

## Project structure

```
src/main/java/com/example/
├── controller/     # @RestController — HTTP boundary only
├── service/        # @Service — all business logic
├── repository/     # @Repository — data access only
├── model/          # @Entity / domain objects
├── dto/            # Request/response POJOs (records preferred)
├── mapper/         # MapStruct mappers between entity ↔ dto
├── exception/      # Custom exceptions + @ControllerAdvice
└── config/         # @Configuration classes
```

## Dependency injection

Always use **constructor injection**. Never `@Autowired` on fields.

```java
@Service
@RequiredArgsConstructor          // Lombok — generates constructor
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

## Exception handling

Use `@ControllerAdvice` with `ProblemDetail` (RFC 9457, Spring 6+):

```java
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    ProblemDetail handleNotFound(ResourceNotFoundException ex) {
        var pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Resource Not Found");
        return pd;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        var pd = ProblemDetail.forStatus(HttpStatus.UNPROCESSABLE_ENTITY);
        pd.setTitle("Validation Failed");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .toList());
        return pd;
    }
}
```

## Validation

Use Bean Validation on DTOs, not in service methods:

```java
public record CreateOrderRequest(
    @NotBlank String customerId,
    @NotEmpty List<@Valid OrderItem> items,
    @Positive BigDecimal totalAmount
) {}

// Controller
@PostMapping("/orders")
ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest req) { ... }
```

## Logging

Use SLF4J with `@Slf4j` (Lombok). Never `System.out.println`.

```java
@Slf4j
@Service
public class OrderService {
    public Order process(String id) {
        log.info("Processing order id={}", id);          // structured params, not concatenation
        log.debug("Order details: {}", order);
        log.error("Failed to process order id={}", id, ex);  // pass exception as last arg
    }
}
```

Log at the right level: ERROR = needs attention now, WARN = degraded but recoverable, INFO = key business events, DEBUG = diagnostic detail.

## REST API conventions

- Use nouns for resources: `/orders`, `/orders/{id}`, `/orders/{id}/items`
- Return `201 Created` + `Location` header on POST
- Return `204 No Content` on successful DELETE
- Use `@PatchMapping` for partial updates, `@PutMapping` for full replace
- Page list endpoints: use `Pageable` parameter + return `Page<T>`

## Supporting references

- Testing (JUnit 5, MockMvc, Testcontainers): [testing.md](testing.md)
- Security (JWT, method security, CORS): [security.md](security.md)
- Configuration (profiles, @ConfigurationProperties, secrets): [configuration.md](configuration.md)
- HTTP service clients (@HttpExchange, registry, Boot 4 properties): [http-service-client.md](http-service-client.md)
