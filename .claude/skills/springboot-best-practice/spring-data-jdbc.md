# Spring Data JDBC Reference

Source: https://docs.spring.io/spring-data/relational/reference/jdbc.html

---

## Key Design Principles

Spring Data JDBC is an intentionally simpler alternative to JPA:

- **No lazy loading** — entities are fully loaded when fetched
- **No dirty tracking** — every `save()` issues an UPDATE (or DELETE + INSERT for referenced entities)
- **No first-level cache** — each call hits the database
- **Aggregate-oriented** — models Domain-Driven Design aggregates; each aggregate has one root

These constraints make behaviour predictable, but require deliberate aggregate design.

---

## Dependency

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jdbc</artifactId>
</dependency>
```

---

## Repository Interfaces

```java
// Basic CRUD
public interface OrderRepository extends CrudRepository<Order, Long> { }

// CRUD with List return types (preferred over Iterable)
public interface OrderRepository extends ListCrudRepository<Order, Long> { }

// CRUD + pagination and sorting
public interface OrderRepository extends ListCrudRepository<Order, Long>,
                                         PagingAndSortingRepository<Order, Long> { }
```

`ListCrudRepository` is the practical default — `findAll()` returns `List<T>` instead of `Iterable<T>`.

---

## Mapping Annotations

### Core

| Annotation | Purpose |
|---|---|
| `@Table("name")` | Maps class to a specific table name |
| `@Column("name")` | Maps field to a specific column name |
| `@Id` | Marks the primary key |
| `@Transient` | Excludes field from persistence |
| `@Version` | Optimistic locking — auto-incremented on update |
| `@ReadOnlyProperty` | Read from DB but never written |
| `@InsertOnlyProperty` | Written on INSERT only, ignored on UPDATE (aggregate root only) |

### Embedded Objects

```java
@Table("PERSON")
class Person {
    @Id Long id;

    @Embedded.Nullable          // columns are inlined into PERSON table
    Address address;

    @Embedded.Nullable(prefix = "billing_")   // prefix avoids column clashes
    Address billingAddress;
}

class Address {
    String street;
    String city;
}
// Columns: ID, STREET, CITY, BILLING_STREET, BILLING_CITY
```

`@Embedded.Nullable` → property is `null` when all columns are null.
`@Embedded(onEmpty = USE_EMPTY)` → always creates an instance even with all-null columns.

### Collections (owned relationships)

```java
class Order {
    @Id Long id;

    // FK column ORDER_ID on ORDER_ITEM table, default naming
    Set<OrderItem>  items;

    // Explicit FK column name
    @MappedCollection(idColumn = "ORDER_ID")
    Set<OrderItem> items;

    // List needs an index column
    @MappedCollection(idColumn = "ORDER_ID", keyColumn = "ITEM_IDX")
    List<OrderItem> items;

    // Map needs a key column
    @MappedCollection(idColumn = "ORDER_ID", keyColumn = "ITEM_KEY")
    Map<String, OrderItem> itemsByKey;
}
```

Owned collections are **deleted and reinserted** on every `save()`.

### Cross-Aggregate References

Use `AggregateReference` to reference another aggregate's root without ownership:

```java
class Order {
    @Id Long id;
    AggregateReference<Customer, Long> customerId; // stores FK only
}

// Setting a reference
order.setCustomerId(AggregateReference.to(customer.getId()));

// Resolving the reference requires an explicit repository call
Customer customer = customerRepository.findById(order.getCustomerId().getId()).orElseThrow();
```

### Composite IDs

```java
@Table("ORDER_ITEM")
record OrderItem(
    @Id @Embedded.Nullable OrderItemId id,
    int quantity
) {}

record OrderItemId(Long orderId, Long itemId) {}
```

---

## ID Generation

| Scenario | Behaviour |
|---|---|
| Auto-increment column | DB generates value; Spring Data reads it back after INSERT |
| `@Sequence("SEQ_NAME")` on `@Id` | Fetches next value from named DB sequence before INSERT |
| No auto-increment, no sequence | Spring Data assumes caller sets the ID; `null`/`0` → treated as new |
| UUID set by caller | Entity is always treated as new — pair with `@Version` (starts at `null`) to mark as persisted after first save |

---

## Saving & Loading Aggregates

### Save semantics

```java
// New entity (id is null/0): INSERT root, then INSERT all referenced entities
Order saved = orderRepository.save(new Order(...));

// Existing entity: UPDATE root, DELETE all owned refs, re-INSERT owned refs
orderRepository.save(existingOrder);
```

**Implication**: avoid holding stale references after save; always use the returned instance.

### Optimistic locking

```java
@Table("PRODUCT")
class Product {
    @Id Long id;
    String name;

    @Version
    Long version;   // null on new entities; incremented by Spring Data on each update
}
```

If `version` in DB differs from entity at update time → `OptimisticLockingFailureException`.

### Single-query loading (v3.2+, experimental)

Loads a complete aggregate in one SQL instead of N+1 queries. Enable it:

```java
@Bean
JdbcMappingContext jdbcMappingContext(NamingStrategy namingStrategy) {
    JdbcMappingContext ctx = new JdbcMappingContext(namingStrategy);
    ctx.setSingleQueryLoadingEnabled(true);
    return ctx;
}
```

Restrictions: no nested collections, no `Map`, no `AggregateReference`, no embedded entities, DB must support window functions (H2 and HSQL excluded).

---

## Query Methods

### Derived queries

```java
public interface ProductRepository extends ListCrudRepository<Product, Long> {
    List<Product> findByName(String name);
    List<Product> findByPriceGreaterThanOrderByNameAsc(BigDecimal price);
    Optional<Product> findBySkuCode(String skuCode);
    boolean existsBySkuCode(String skuCode);
    long countByCategory(String category);
}
```

Supported keywords: `And`, `Or`, `Between`, `LessThan`, `GreaterThan`, `IsNull`, `Like`, `StartingWith`, `Containing`, `EndingWith`, `In`, `True`, `False`, `IgnoreCase`, `OrderBy`.

**Limitation**: only simple properties on the aggregate root — no joins or nested properties.

### @Query

```java
public interface OrderRepository extends ListCrudRepository<Order, Long> {

    @Query("SELECT * FROM order WHERE status = :status")
    List<Order> findByStatus(@Param("status") String status);

    // With SpEL for dynamic table names
    @Query("SELECT * FROM #{tableName} WHERE id = :id")
    Optional<Order> findDynamic(@Param("id") Long id);

    // Custom RowMapper
    @Query(value = "SELECT ...", rowMapperClass = OrderSummaryRowMapper.class)
    List<OrderSummary> findSummaries();

    // Modifying query
    @Modifying
    @Query("UPDATE order SET status = :status WHERE id = :id")
    boolean updateStatus(@Param("id") Long id, @Param("status") String status);
}
```

`@Query` does **not** support `Pageable`, `Sort`, or `PageRequest` parameters — apply SQL LIMIT/OFFSET manually.

`@Modifying` return types: `void`, `int` (rows affected), `boolean` (at least one row affected).
Note: modifying queries bypass lifecycle callbacks and auditing.

### Streaming results

```java
@Query("SELECT * FROM large_table WHERE status = :status")
Stream<Order> streamByStatus(@Param("status") String status);

// Must close the stream
try (Stream<Order> stream = repo.streamByStatus("PENDING")) {
    stream.forEach(this::process);
}
```

### Pagination

```java
Page<Order>  findByStatus(String status, Pageable pageable);
Slice<Order> findByCustomerId(Long customerId, Pageable pageable);
List<Order>  findByStatus(String status, Pageable pageable);
```

Usage:

```java
Pageable page = PageRequest.of(0, 20, Sort.by("createdAt").descending());
Page<Order> result = orderRepository.findByStatus("OPEN", page);
```

---

## JdbcAggregateTemplate

Direct template API — useful for operations not exposed by repositories:

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    private final JdbcAggregateTemplate template;

    public Order insert(Order order) {
        return template.insert(order);   // always INSERT, no existence check
    }

    public Order update(Order order) {
        return template.update(order);   // always UPDATE
    }

    public Order upsert(Order order) {
        return template.upsert(order);   // single-round-trip DB upsert
    }

    public Optional<Order> findByName(String name) {
        return template.findOne(
            query(where("name").is(name)),
            Order.class
        );
    }

    public List<Order> findExpensive(BigDecimal threshold) {
        return template.findAll(
            query(where("total").greaterThan(threshold)),
            Order.class
        );
    }
}
```

`Criteria` operators: `is`, `not`, `isNull`, `isNotNull`, `greaterThan`, `greaterThanOrEquals`, `lessThan`, `lessThanOrEquals`, `in`, `notIn`, `like`.

---

## Custom Converters

```java
@WritingConverter
public class MoneyToLongConverter implements Converter<Money, Long> {
    @Override
    public Long convert(Money source) {
        return source.getAmountMinorLong();
    }
}

@ReadingConverter
public class LongToMoneyConverter implements Converter<Long, Money> {
    @Override
    public Money convert(Long source) {
        return Money.ofMinor(CurrencyUnit.EUR, source);
    }
}

// Registration
@Configuration
public class JdbcConfig extends AbstractJdbcConfiguration {
    @Override
    protected List<?> userConverters() {
        return List.of(new MoneyToLongConverter(), new LongToMoneyConverter());
    }
}
```

Use `JdbcValue.of(value, Types.VARCHAR)` in a writing converter when you need to specify the JDBC type explicitly.

---

## Auditing

```java
@Configuration
@EnableJdbcAuditing
public class JdbcConfig extends AbstractJdbcConfiguration {

    @Bean
    AuditorAware<String> auditorProvider() {
        // Return current user from security context
        return () -> Optional.ofNullable(SecurityContextHolder.getContext())
            .map(SecurityContext::getAuthentication)
            .map(Authentication::getName);
    }
}
```

Annotate entity fields:

```java
@Table("ORDER")
class Order {
    @Id Long id;

    @CreatedDate
    LocalDateTime createdAt;

    @LastModifiedDate
    LocalDateTime updatedAt;

    @CreatedBy
    String createdBy;

    @LastModifiedBy
    String updatedBy;

    @Version
    Long version;
}
```

The corresponding DB columns must exist. For new entities the `@CreatedDate` / `@CreatedBy` values are set; on update only `@LastModifiedDate` / `@LastModifiedBy` change.

---

## Lifecycle Events / Entity Callbacks

Spring Data JDBC publishes application events and supports `EntityCallback` beans. Prefer callbacks — they run synchronously in the same transaction.

```java
@Component
public class OrderCallbacks
        implements BeforeConvertCallback<Order>,
                   BeforeSaveCallback<Order>,
                   AfterSaveCallback<Order> {

    @Override
    public Order onBeforeConvert(Order order, SqlIdentifier table) {
        // Runs before the entity is converted to a row map; mutate the entity
        if (order.getReference() == null) {
            order.setReference(UUID.randomUUID().toString());
        }
        return order;
    }

    @Override
    public Order onBeforeSave(Order order, MutableAggregateChange<Order> change) {
        // Runs after conversion; last chance to modify before SQL is issued
        return order;
    }

    @Override
    public Order onAfterSave(Order order, AggregateChange<Order> change) {
        // Runs after INSERT/UPDATE; entity reflects persisted state
        return order;
    }
}
```

Available callbacks: `BeforeConvertCallback`, `BeforeSaveCallback`, `AfterSaveCallback`, `AfterLoadCallback`, `BeforeDeleteCallback`, `AfterDeleteCallback`.

---

## Configuration

```java
@Configuration
@EnableJdbcRepositories(basePackages = "com.example.repository")
public class JdbcConfig extends AbstractJdbcConfiguration {

    @Bean
    DataSource dataSource() { ... }

    @Bean
    NamedParameterJdbcTemplate namedParameterJdbcTemplate(DataSource ds) {
        return new NamedParameterJdbcTemplate(ds);
    }

    // Custom naming strategy (default: camelCase → SNAKE_CASE)
    @Bean
    NamingStrategy namingStrategy() {
        return NamingStrategy.DEFAULT;  // or a custom implementation
    }
}
```

Spring Boot auto-configures all of the above when `spring-boot-starter-data-jdbc` is on the classpath — you only need `AbstractJdbcConfiguration` when overriding converters or naming.

---

## Common Pitfalls

- **`save()` always replaces owned collections**: do not call `save()` on a partially-loaded aggregate; always load, mutate, then save the full aggregate root.
- **No `@OneToMany` / `@ManyToOne`**: Spring Data JDBC has no JPA-style relationship annotations. Collections inside an aggregate are owned; cross-aggregate links use `AggregateReference`.
- **`@Modifying` bypasses callbacks**: auditing fields (`@LastModifiedDate`, etc.) will not be updated on bulk UPDATE queries — update them manually in the SQL.
- **Pagination with `@Query`**: `Pageable` is not supported in string queries; use `LIMIT :limit OFFSET :offset` with explicit parameters.
- **Mutable aggregate state after save**: always use the entity returned by `save()` — the original instance may not reflect the generated ID or incremented `@Version`.
- **`AggregateReference` is not eagerly loaded**: resolving it requires an explicit repository call; there is no fetch-join equivalent.
