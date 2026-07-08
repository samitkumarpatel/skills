# Spring Modulith

References:
- [Spring Modulith](https://docs.spring.io/spring-modulith/reference/)
- [Fundamentals](https://docs.spring.io/spring-modulith/reference/fundamentals.html)
- [Verification](https://docs.spring.io/spring-modulith/reference/verification.html)
- [Application Events](https://docs.spring.io/spring-modulith/reference/events.html)
- [Testing](https://docs.spring.io/spring-modulith/reference/testing.html)
- [Moments](https://docs.spring.io/spring-modulith/reference/moments.html)
- [Documentation](https://docs.spring.io/spring-modulith/reference/documentation.html)
- [Runtime](https://docs.spring.io/spring-modulith/reference/runtime.html)

---

## What is Spring Modulith?

Spring Modulith is an opinionated toolkit for building domain-driven, modular Spring Boot applications. It enforces clear module boundaries, verifies architectural rules, enables loosely coupled event-based inter-module communication, and generates living documentation — all without requiring a microservice split.

---

## Dependency setup

Import the BOM, then pick the starters you need:

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.springframework.modulith</groupId>
      <artifactId>spring-modulith-bom</artifactId>
      <version>2.1.0</version>
      <scope>import</scope>
      <type>pom</type>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <!-- Core module model -->
  <dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-core</artifactId>
  </dependency>

  <!-- Event publication registry (pick one persistence backend) -->
  <dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-jpa</artifactId>   <!-- or -jdbc, -mongodb, -neo4j -->
  </dependency>

  <!-- Runtime support and actuator -->
  <dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-runtime</artifactId>
    <scope>runtime</scope>
  </dependency>

  <!-- Integration testing -->
  <dependency>
    <groupId>org.springframework.modulith</groupId>
    <artifactId>spring-modulith-starter-test</artifactId>
    <scope>test</scope>
  </dependency>
</dependencies>
```

---

## Fundamentals — Application Modules

### Package structure

Direct sub-packages of the main application package are **application modules**. Public types form the module's API; package-private types are internal and inaccessible to other modules.

```
com.example
├── Application.java                   ← main class
├── com.example.order                  ← "order" module
│   ├── OrderManagement.java           ← public API
│   └── internal/
│       └── OrderRepository.java       ← internal (sub-package = internal)
└── com.example.inventory              ← "inventory" module
    ├── InventoryManagement.java       ← public API
    └── SomethingInternal.java         ← package-private = internal
```

### Viewing the module model

```java
var modules = ApplicationModules.of(Application.class);
modules.forEach(System.out::println);
```

Output example:
```
## example.order ##
> Logical name: order
> Base package: example.order
> Spring beans:
  + ….OrderManagement
  o ….OrderRepository          ← internal
```

### Named interfaces — exposing additional packages

Use `@NamedInterface` to expose a sub-package beyond the base package:

```java
// package-info.java in example.order.spi
@org.springframework.modulith.NamedInterface("spi")
package example.order.spi;
```

Reference it in a dependent module's allowed dependencies:

```java
// package-info.java in example.inventory
@org.springframework.modulith.ApplicationModule(
    allowedDependencies = "order :: spi"   // only the spi interface, not order internals
)
package example.inventory;
```

### Explicit allowed dependencies

Declare exactly which modules a module may depend on:

```java
@org.springframework.modulith.ApplicationModule(
    allowedDependencies = "order"
)
package example.inventory;
```

### Open modules

Allow all types (including internals) to be accessed from any module — useful for shared infrastructure:

```java
// package-info.java
@org.springframework.modulith.ApplicationModule(type = Type.OPEN)
package example.shared;
```

### @Modulithic on the main class

Use `@Modulithic` to set a system name and define shared modules that are always included in integration tests:

```java
@Modulithic(systemName = "My Shop", sharedModules = "shared")
@SpringBootApplication
class Application { ... }
```

---

## Verification

Call `verify()` in a test to enforce architectural rules. This is typically a single test that runs as part of every CI build:

```java
class ModularityTests {

    ApplicationModules modules = ApplicationModules.of(Application.class);

    @Test
    void verifiesModularStructure() {
        modules.verify();
    }
}
```

**What `verify()` enforces:**

| Rule | Description |
|---|---|
| No module cycles | Dependencies between modules form a directed acyclic graph |
| No internal access | References into another module's internal packages are rejected |
| Explicit dependency compliance | If `allowedDependencies` is set, unlisted dependencies are rejected |

### Accessing violations before throwing

```java
modules.detectViolations()
    .filter(violation -> ...)
    .throwIfPresent();
```

---

## Application Events — inter-module communication

Modules communicate through Spring application events rather than direct service calls. This removes compile-time coupling between modules.

### Publishing events

```java
@Service
@RequiredArgsConstructor
public class OrderManagement {

    private final ApplicationEventPublisher events;

    @Transactional
    public void complete(Order order) {
        // business logic...
        events.publishEvent(new OrderCompleted(order.getId()));
    }
}
```

### Listening with @ApplicationModuleListener

`@ApplicationModuleListener` combines `@TransactionalEventListener` + `@Async` + `@Transactional(REQUIRES_NEW)` — the listener runs after the publishing transaction commits, in its own transaction:

```java
@Component
class InventoryManagement {

    @ApplicationModuleListener
    void on(OrderCompleted event) {
        // reduce stock, etc.
    }
}
```

### Event publication registry

Spring Modulith persists each event publication and tracks completion per listener. If a listener fails or the application crashes, publications remain in an incomplete state and can be resubmitted.

**Completion modes** (`spring.modulith.events.completion-mode`):

| Mode | Behaviour |
|---|---|
| `UPDATE` (default) | Sets a completion timestamp; entry stays in the registry |
| `DELETE` | Entry deleted on completion |
| `ARCHIVE` | Entry copied to an archive table; original removed |

**Re-publish incomplete events on restart:**

```yaml
spring:
  modulith:
    events:
      republish-outstanding-events-on-restart: true
```

**Resubmit failed publications programmatically:**

```java
failedEventPublications.resubmit(
    ResubmissionOptions.defaults()
        .withBatchSize(10)
        .withMinAge(Duration.ofMinutes(5))
);
```

### Externalizing events to a message broker

Annotate an event with `@Externalized` to publish it to Kafka, AMQP, JMS, etc.:

```java
@Externalized("orders.completed::#{#this.orderId()}")
record OrderCompleted(String orderId) {}
```

Pattern: `$target::$routingKey` — both support SpEL with the event as the root object.

Supported brokers and their starters:

| Broker | Artifact |
|---|---|
| Kafka | `spring-modulith-events-kafka` |
| AMQP (RabbitMQ) | `spring-modulith-events-amqp` |
| JMS | `spring-modulith-events-jms` |

---

## Moments — Passage of Time Events

`spring-modulith-moments` fires temporal events at regular intervals so modules can react to time passing without polling or scheduling their own jobs.

```xml
<dependency>
  <groupId>org.springframework.modulith</groupId>
  <artifactId>spring-modulith-moments</artifactId>
</dependency>
```

**Available events:** `HourHasPassed`, `DayHasPassed`, `WeekHasPassed`, `MonthHasPassed`, `QuarterHasPassed`, `YearHasPassed`.

```java
@Component
class ReportingModule {

    @ApplicationModuleListener
    void on(MonthHasPassed event) {
        // generate monthly report
    }

    @ApplicationModuleListener
    void on(DayHasPassed event) {
        // daily digest
    }
}
```

**Configuration:**

```yaml
spring:
  modulith:
    moments:
      granularity: hours          # or "days" to skip hourly events
      zone-id: Europe/Berlin
      enable-time-machine: true   # enables TimeMachine for tests
```

Enable TimeMachine in tests to fast-forward time and trigger intermediate events without sleeping:

```java
@ApplicationModuleTest
class ReportingModuleTest {

    @Autowired TimeMachine timeMachine;

    @Test
    void triggersMonthlyReport(Scenario scenario) {
        scenario.stimulate(() -> timeMachine.shiftBy(Duration.ofDays(32)))
            .andWaitForEventOfType(MonthHasPassed.class)
            .toArrive();
    }
}
```

---

## Runtime Support

Add `spring-modulith-runtime` (scope `runtime`) to enable module-aware startup initialisation:

```java
@Component
class InventoryInitializer implements ApplicationModuleInitializer {

    @Override
    public void initialize() {
        // runs on ApplicationStartedEvent, in module dependency order
    }
}
```

**Module-aware Flyway migrations** (Spring Modulith 2.0+):

```yaml
spring:
  modulith:
    runtime:
      flyway-enabled: true
```

Migration scripts live in `db/migration/$moduleIdentifier/` per module; each module gets its own schema history table.

Enable module structure verification on startup:

```yaml
spring:
  modulith:
    runtime:
      verification-enabled: true
```

---

## Documentation Generation

Generate PlantUML diagrams and module canvases in a test:

```java
class DocumentationTests {

    ApplicationModules modules = ApplicationModules.of(Application.class);

    @Test
    void writeDocumentationSnippets() {
        new Documenter(modules)
            .writeModulesAsPlantUml()            // all modules in one diagram
            .writeIndividualModulesAsPlantUml()  // per-module diagram with dependencies
            .writeModuleCanvases()               // tabular canvas per module
            .writeAggregatingDocument();         // single all-docs.adoc linking everything
    }
}
```

Each **module canvas** contains: base package, Spring beans, aggregate roots, published events, listened-to events, and `@ConfigurationProperties` classes.

Output lands in `{build-dir}/spring-modulith-docs/`.

---

## Do not

- Let modules call into each other's internal packages — enforce this with `verify()`
- Use direct service-to-service calls across module boundaries for decoupled flows — prefer `ApplicationEventPublisher`
- Forget to run the modularity verification test in CI — it is the architectural safety net
- Store event payloads that are not serializable — the publication registry persists them as JSON
