# Spring Boot Configuration Patterns

## @ConfigurationProperties — prefer over @Value for structured config

```java
@ConfigurationProperties(prefix = "app.payment")
@Validated
public record PaymentProperties(
    @NotBlank String apiUrl,
    @NotBlank String apiKey,
    @Positive int timeoutSeconds,
    RetryProperties retry
) {
    public record RetryProperties(
        @Min(1) int maxAttempts,
        @Positive long backoffMs
    ) {}
}
```

Register it:
```java
@SpringBootApplication
@ConfigurationPropertiesScan    // picks up all @ConfigurationProperties
public class Application { ... }
```

`application.yml`:
```yaml
app:
  payment:
    api-url: ${PAYMENT_API_URL}
    api-key: ${PAYMENT_API_KEY}
    timeout-seconds: 30
    retry:
      max-attempts: 3
      backoff-ms: 500
```

Use `@Value` only for a single, isolated property — not for groups of related settings.

`application.yml` (shared):
```yaml
spring:
  datasource:
    url: ${DB_URL}
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}

logging:
  level:
    root: INFO
```

Always read secrets from environment variables or a secrets manager:

```yaml
# Good — reads from env at runtime
spring:
  datasource:
    password: ${DB_PASSWORD}

# Bad — secret committed to source control
spring:
  datasource:
    password: supersecret123
```

## Database migrations

Use Flyway (preferred) or Liquibase. Never let JPA auto-create schema in production.

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: validate       # validate schema matches entities; never create/update in prod
  flyway:
    enabled: true
    locations: classpath:db/migration
```

Migration files follow `V{version}__{description}.sql`:
```
src/main/resources/db/migration/
├── V1__create_orders_table.sql
├── V2__add_customer_index.sql
└── V3__add_status_column.sql
```

## Actuator

Expose only what you need.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
```