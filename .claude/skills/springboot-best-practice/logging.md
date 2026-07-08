# Spring Boot Logging Patterns

Reference: [Spring Boot — Logging](https://docs.spring.io/spring-boot/reference/features/logging.html)

## Default setup

Spring Boot uses **Commons Logging** internally and defaults to **Logback** when using starters. No extra dependency is needed — `spring-boot-starter` pulls it in. Use SLF4J with `@Slf4j` (Lombok) in application code.

```java
@Slf4j
@Service
public class OrderService {
    public Order process(String id) {
        log.info("Processing order id={}", id);
        log.debug("Order details: {}", order);
        log.error("Failed to process order id={}", id, ex);  // exception as last arg
    }
}
```

Always pass structured parameters — never concatenate strings:

```java
// Good
log.info("Order created id={} customer={}", order.getId(), order.getCustomerId());

// Bad — allocates string even when the level is disabled
log.info("Order created id=" + order.getId());
```

## Log format

Spring Boot's default console output:

```
2026-06-10T16:33:37.305Z  INFO 53358 --- [myapp] [main] o.s.b.d.f.MyApplication : Starting MyApplication
```

Fields in order: date/time · log level · PID · `---` separator · app name (if `spring.application.name` is set) · thread name · logger name (abbreviated) · message.

## Log levels

| Level | When to use |
|---|---|
| `ERROR` | Needs immediate attention — unexpected failure, data loss risk |
| `WARN` | Degraded but recoverable — retried request, fallback used |
| `INFO` | Key business events — order created, payment processed |
| `DEBUG` | Diagnostic detail — request payloads, cache hits, query timings |
| `TRACE` | Very verbose — method entry/exit, SQL parameter values |

Configure via `application.yml`:

```yaml
logging:
  level:
    root: info
    com.example.myapp: debug          # your package
    org.springframework.web: warn     # reduce framework noise
    org.hibernate.SQL: debug          # log SQL statements
```

Or via environment variable (dots become underscores, all caps):

```bash
LOGGING_LEVEL_COM_EXAMPLE_MYAPP=DEBUG
```

## Log groups

Group multiple loggers under a single name for easier level control:

```yaml
logging:
  group:
    database: org.hibernate,org.springframework.jdbc.core
  level:
    database: debug
    web: warn     # built-in group
```

**Pre-defined groups:**

| Group | Loggers covered |
|---|---|
| `web` | `org.springframework.core.codec`, `org.springframework.http`, `org.springframework.web`, and Boot web servlet beans |
| `sql` | `org.springframework.jdbc.core`, `org.hibernate.SQL`, `LoggerListener` |

## File output

By default Spring Boot logs to the console only. Enable file logging:

```yaml
logging:
  file:
    name: logs/myapp.log   # specific file
    # path: /var/log       # OR directory — writes spring.log there
```

**Logback file rotation defaults** (override as needed):

```yaml
logging:
  logback:
    rollingpolicy:
      file-name-pattern: ${LOG_FILE}.%d{yyyy-MM-dd}.%i.gz
      max-file-size: 10MB
      max-history: 7
      total-size-cap: 1GB
      clean-history-on-start: false
```

## Structured / JSON logging (Spring Boot 3.4+)

Spring Boot has built-in support for structured logging — no extra library needed. Choose a format per output:

```yaml
logging:
  structured:
    format:
      console: logstash   # or ecs, gelf, or a fully-qualified class name
      file: ecs
```

**Supported formats:**

| Format | Key | Example use case |
|---|---|---|
| Elastic Common Schema | `ecs` | Elastic Stack (Kibana) |
| Graylog Extended Log Format | `gelf` | Graylog |
| Logstash JSON | `logstash` | Logstash / OpenSearch |
| Custom class | FQCN | Any other sink |

**ECS service metadata:**

```yaml
logging:
  structured:
    ecs:
      service:
        name: order-service      # defaults to spring.application.name
        version: 1.0.0           # defaults to spring.application.version
        environment: production
```

**Customise JSON fields** (include/exclude/rename/add):

```yaml
logging:
  structured:
    json:
      exclude: log.level
      rename:
        process.id: pid
      add:
        team: platform
```

## MDC context (trace IDs, per-request context)

```java
try (var ignored = MDC.putCloseable("orderId", order.getId())) {
    log.info("Starting payment processing");
    paymentService.charge(order);
    log.info("Payment complete");
}
// MDC entry removed automatically on close
```

In structured output, MDC key-value pairs appear as top-level JSON fields — useful for filtering in Kibana / Grafana Loki.

Add MDC to the console pattern:

```yaml
logging:
  pattern:
    level: "orderId:%X{orderId} %5p"
```

## Profile-specific Logback configuration

Use `logback-spring.xml` (not `logback.xml`) to access Spring's `<springProfile>` and `<springProperty>` extensions:

```xml
<springProfile name="!prod">
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    <root level="DEBUG"><appender-ref ref="CONSOLE"/></root>
</springProfile>

<springProfile name="prod">
    <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
        <!-- use structured logging instead of logstash-logback-encoder -->
    </appender>
    <root level="INFO"><appender-ref ref="JSON"/></root>
</springProfile>
```

Read Spring properties inside the XML:

```xml
<springProperty scope="context" name="appName"
    source="spring.application.name" defaultValue="app"/>
```

## Console debug / trace mode

```bash
# Enable debug mode (key framework components log at DEBUG)
java -jar myapp.jar --debug

# Enable trace mode (full framework trace)
java -jar myapp.jar --trace
```

Or in `application.yml`:

```yaml
debug: true
```

## Do not

- Use `System.out.println` or `ex.printStackTrace()`
- Concatenate strings in log calls — always use `{}` parameterised placeholders
- Log sensitive data: passwords, tokens, full card numbers, PII
- Log at `ERROR` for expected business conditions (e.g. "not found") — use `WARN` or `INFO`
- Guard debug calls with `if (log.isDebugEnabled())` unless the argument itself is expensive to compute
- Use `logback.xml` when you need Spring profile or property support — use `logback-spring.xml` instead
