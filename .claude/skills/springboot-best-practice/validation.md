# Spring Boot Validation Patterns

Reference: [Spring Boot — Validation](https://docs.spring.io/spring-boot/reference/io/validation.html)

## Auto-configuration

Bean Validation is automatically enabled as long as a JSR-303 implementation (Hibernate Validator) is on the classpath via `spring-boot-starter-validation`. No explicit `@EnableValidation` annotation is needed.

## Request body validation (DTOs)

Put Jakarta constraints on request DTOs, not inside service methods. Trigger validation in the controller with `@Valid`:

```java
public record CreateOrderRequest(
    @NotBlank String customerId,
    @NotEmpty List<@Valid OrderItem> items,
    @Positive BigDecimal totalAmount
) {}

public record OrderItem(
    @NotBlank String productId,
    @Min(1) int quantity
) {}

@PostMapping("/orders")
ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest req) { ... }
```

Validation failures throw `MethodArgumentNotValidException` — handle centrally in `@ControllerAdvice` (see [exception-handling.md](exception-handling.md)).

## Method-level validation on service beans

Annotate the class with `@Validated` to enable inline constraint annotations on method parameters and return values. Spring Boot auto-configures this — no extra setup required.

```java
import jakarta.validation.constraints.Size;
import org.springframework.validation.annotation.Validated;

@Service
@Validated
public class ArchiveService {

    public Archive findByCodeAndAuthor(@Size(min = 8, max = 10) String code, Author author) {
        return ...
    }
}
```

Use this for service-layer contracts that must hold regardless of which caller invokes the method.

## Validating path and query parameters

Add `@Validated` to the controller class and apply constraints directly on method parameters:

```java
@Validated
@RestController
public class OrderController {

    @GetMapping("/orders/{id}")
    ResponseEntity<OrderResponse> get(@PathVariable @NotBlank String id) { ... }

    @GetMapping("/orders")
    ResponseEntity<Page<OrderResponse>> list(
        @RequestParam @Min(0) int page,
        @RequestParam @Max(100) int size) { ... }
}
```

## Common constraints

| Constraint | Use case |
|---|---|
| `@NotNull` | Field must not be null |
| `@NotBlank` | String must have text (not null / empty / whitespace) |
| `@NotEmpty` | Collection or String must not be empty |
| `@Size(min, max)` | String / Collection length bounds |
| `@Min` / `@Max` | Numeric lower / upper bounds |
| `@Positive` / `@PositiveOrZero` | Number > 0 or >= 0 |
| `@Email` | Valid e-mail format |
| `@Pattern(regexp)` | Regex match |
| `@Valid` | Cascade validation into nested objects or collections |
| `@Validated` | Spring's variant — also supports validation groups |

## Custom constraint messages via MessageSource

Spring Boot integrates `MessageSource` into Bean Validation. Define constraint messages in `messages.properties` instead of hardcoding them:

```properties
# src/main/resources/messages.properties
jakarta.validation.constraints.NotBlank.message=Field must not be blank
jakarta.validation.constraints.Size.message=Size must be between {min} and {max}
order.customerId.notBlank=Customer ID is required
```

Reference a custom key in the annotation:

```java
public record CreateOrderRequest(
    @NotBlank(message = "{order.customerId.notBlank}") String customerId
) {}
```

## Custom constraint

```java
@Documented
@Constraint(validatedBy = ValidCurrencyValidator.class)
@Target({ FIELD })
@Retention(RUNTIME)
public @interface ValidCurrency {
    String message() default "Invalid ISO 4217 currency code";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class ValidCurrencyValidator implements ConstraintValidator<ValidCurrency, String> {
    @Override
    public boolean isValid(String value, ConstraintValidatorContext ctx) {
        return value != null && Currency.getAvailableCurrencies()
            .stream().anyMatch(c -> c.getCurrencyCode().equals(value));
    }
}
```

## Validation groups (conditional validation)

```java
public record PaymentRequest(
    @NotNull(groups = Create.class) String id,
    @NotBlank String cardNumber
) {
    public interface Create {}
}

@PostMapping
ResponseEntity<?> create(
    @Validated(PaymentRequest.Create.class) @RequestBody PaymentRequest req) { ... }
```

## Custom ValidatorFactory configuration

To fine-tune the `ValidatorFactory`, define a `ValidationConfigurationCustomizer` bean. Multiple customizers are applied in `@Order` sequence:

```java
@Bean
ValidationConfigurationCustomizer customizer() {
    return config -> config
        .messageInterpolator(new ParameterMessageInterpolator());
}
```

## Do not

- Validate inside service methods when Bean Validation can express the constraint
- Duplicate validation logic in both the controller and the service
- Put `@Valid` on repository method parameters — validate at the controller boundary
- Forget `@Validated` at the class level when using method-level constraints on service beans — without it, constraints are silently ignored
