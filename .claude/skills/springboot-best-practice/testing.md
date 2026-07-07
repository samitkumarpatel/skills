# Spring Boot Testing Patterns

## Test layers — use the right slice

| What you're testing | Annotation | Loads |
|---|---|---|
| Controller (HTTP layer) | `@WebMvcTest(MyController.class)` | MVC infra + security only |
| Repository (SQL) | `@DataJpaTest` | JPA + in-memory DB |
| REST client (`@HttpExchange`) | `@RestClientTest(MyClient.class)` | RestClient wiring only |
| JSON serialization | `@JsonTest` | Jackson mapper only |
| Full application | `@SpringBootTest` | Full context |
| Pure logic | none (plain JUnit) | Nothing |

Avoid `@SpringBootTest` for unit tests — it's slow. Prefer slices or plain JUnit.

---

## Controller tests with @WebMvcTest

Use `@WebMvcTest` to load only the MVC layer. Use `@MockitoBean` (Spring Framework 6.2+, replaces `@MockBean`) to replace service dependencies.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean  OrderService orderService;

    @Test
    void createOrder_returns201() throws Exception {
        given(orderService.create(any())).willReturn(new OrderResponse("ord-1", "PENDING"));

        mockMvc.perform(post("/orders")
                .contentType(APPLICATION_JSON)
                .content("""
                    {"customerId":"cust-1","items":[],"totalAmount":10}
                    """))
            .andExpect(status().isCreated())
            .andExpect(header().exists("Location"))
            .andExpect(jsonPath("$.id").value("ord-1"));
    }

    @Test
    void createOrder_invalidBody_returns422() throws Exception {
        mockMvc.perform(post("/orders")
                .contentType(APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isUnprocessableEntity())
            .andExpect(jsonPath("$.title").value("Validation Failed"));
    }
}
```

### Modern MockMvc with AssertJ (MockMvcTester — Spring 6.2+)

`MockMvcTester` gives a fluent AssertJ API with no checked exceptions and uniform async handling:

```java
@WebMvcTest(OrderController.class)
class OrderControllerAssertJTest {

    @Autowired MockMvcTester mvc;
    @MockitoBean  OrderService orderService;

    @Test
    void createOrder_returns201() {
        given(orderService.create(any())).willReturn(new OrderResponse("ord-1", "PENDING"));

        assertThat(mvc.post().uri("/orders")
                .contentType(APPLICATION_JSON)
                .content("""{"customerId":"cust-1","items":[],"totalAmount":10}"""))
            .hasStatus(HttpStatus.CREATED)
            .hasHeader("Location")
            .bodyJson().extractingPath("$.id").isEqualTo("ord-1");
    }
}
```

---

## Service unit tests

No Spring context needed — instantiate directly. This is always fastest.

```java
class OrderServiceTest {

    OrderRepository repository = mock(OrderRepository.class);
    PaymentService  payment    = mock(PaymentService.class);
    OrderService    service    = new OrderService(repository, payment);

    @Test
    void process_savesOrderWithProcessedStatus() {
        var order = new Order("ord-1", Status.PENDING);
        given(repository.findById("ord-1")).willReturn(Optional.of(order));

        service.process("ord-1");

        verify(repository).save(argThat(o -> o.getStatus() == Status.PROCESSED));
    }

    @Test
    void process_unknownId_throwsNotFoundException() {
        given(repository.findById("bad-id")).willReturn(Optional.empty());

        assertThatExceptionOfType(ResourceNotFoundException.class)
            .isThrownBy(() -> service.process("bad-id"));
    }
}
```

---

## Repository tests with @DataJpaTest

Uses an in-memory H2 database by default. `@Transactional` rolls back after each test automatically.

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired OrderRepository repository;

    @Test
    void findByCustomerId_returnsMatchingOrders() {
        repository.save(new Order(null, "cust-1", Status.PENDING));
        repository.save(new Order(null, "cust-2", Status.PENDING));

        assertThat(repository.findByCustomerId("cust-1")).hasSize(1);
    }
}
```

To use a real database instead of H2:

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)   // keep the real datasource
class OrderRepositoryRealDbTest { ... }
```

---

## Integration tests with Testcontainers

Use for tests that need a real database, broker, or other external service.

```java
@SpringBootTest
@Testcontainers
class OrderIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url",      postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired OrderService service;

    @Test
    void fullOrderFlow() {
        var order = service.create(new CreateOrderRequest("cust-1", List.of(), BigDecimal.TEN));
        assertThat(order.status()).isEqualTo("PENDING");
    }
}
```

---

## Transaction handling in tests

`@Transactional` on a test rolls back automatically after each test — prefer this for data isolation.

```java
@SpringBootTest
@Transactional                      // auto-rollback after each test
class OrderTransactionalTest {

    @Autowired OrderRepository repository;

    @Test
    void saveOrder_persists() {
        repository.save(new Order(null, "cust-1", Status.PENDING));
        assertThat(repository.count()).isEqualTo(1);
    }   // rolled back — next test starts clean
}
```

Use `@Commit` only when you explicitly need to verify post-commit behavior (e.g., database constraints, audit triggers).

Use `@BeforeTransaction` / `@AfterTransaction` for setup/teardown that must run **outside** the transaction:

```java
@BeforeTransaction
void insertBaseData() { /* insert reference data that must be committed */ }

@AfterTransaction
void cleanUp() { /* delete outside the test transaction */ }
```

---

## Context caching

Spring caches the `ApplicationContext` across tests that share identical configuration. A new context is only loaded when config differs (different beans, profiles, properties).

**Maximize cache hits:**
- Group tests that share context configuration into the same class or extend a common base
- Use `@ActiveProfiles` consistently — mixing profiles across tests creates multiple cached contexts

**Invalidate the cache when necessary:**
```java
@DirtiesContext(classMode = ClassMode.AFTER_EACH_TEST_METHOD)
class StatefulBeanTest { ... }
```

Use `@DirtiesContext` sparingly — it forces a full context reload and slows down the suite.

---

## Bean overriding

### @MockitoBean — replace with a Mockito mock

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @MockitoBean OrderService orderService;  // full mock, all methods return null/empty by default
}
```

### @MockitoSpyBean — wrap real bean, selectively override

```java
@SpringBootTest
class PartialOverrideTest {
    @MockitoSpyBean OrderService orderService;  // real bean, individual methods can be stubbed

    @Test
    void realBehaviorWithOneStubbed() {
        doReturn(List.of()).when(orderService).getPendingOrders();
        // other methods behave normally
    }
}
```

### @TestBean — replace with a hand-crafted test double (no Mockito)

```java
@SpringBootTest
class TestBeanTest {

    @TestBean
    NotificationService notificationService = new FakeNotificationService();

    static class FakeNotificationService implements NotificationService {
        List<String> sent = new ArrayList<>();

        @Override public void send(String msg) { sent.add(msg); }
    }
}
```

---

## Property overrides for tests

```java
@SpringBootTest
@TestPropertySource(properties = {
    "app.payment.api-url=http://localhost:9090",
    "app.payment.timeout-seconds=1"
})
class PaymentServiceTest { ... }
```

Or load from a file:

```java
@TestPropertySource(locations = "classpath:test-overrides.properties")
```

---

## SQL script setup with @Sql

```java
@SpringBootTest
@Transactional
@Sql("/test-data/orders.sql")                   // runs before each test
@Sql(scripts = "/test-data/cleanup.sql",
     executionPhase = AFTER_TEST_METHOD)         // runs after each test
class OrderQueryTest { ... }
```

---

## Spring Security testing

### Setup: apply springSecurity() to MockMvc

```java
@WebMvcTest(OrderController.class)
class SecurityTest {

    @Autowired WebApplicationContext context;
    MockMvc mockMvc;

    @BeforeEach
    void setup() {
        mockMvc = MockMvcBuilders.webAppContextSetup(context)
            .apply(springSecurity())
            .build();
    }
}
```

### Mocking users

```java
// Simple authenticated user
mockMvc.perform(get("/orders").with(user("alice")))

// With role
mockMvc.perform(get("/admin").with(user("admin").roles("ADMIN")))

// Annotation-based (cleaner for many tests)
@Test @WithMockUser(roles = "ADMIN")
void adminEndpoint_returns200() throws Exception {
    mockMvc.perform(get("/admin")).andExpect(status().isOk());
}

@Test
void noUser_returns401() throws Exception {
    mockMvc.perform(get("/orders")).andExpect(status().isUnauthorized());
}
```

### JWT / OAuth2 resource server

```java
// Minimal JWT mock
mockMvc.perform(get("/orders").with(jwt()))

// With specific claims and scope
mockMvc.perform(get("/orders")
    .with(jwt()
        .jwt(j -> j.claim("sub", "alice").claim("scope", "orders:read"))
        .authorities(new SimpleGrantedAuthority("SCOPE_orders:read"))))

// OidcLogin for full OIDC flow
mockMvc.perform(get("/me")
    .with(oidcLogin()
        .idToken(t -> t.claim("email", "alice@example.com"))))
```

### Testing @PreAuthorize on services

```java
@ExtendWith(SpringExtension.class)
@SpringBootTest
class OrderServiceSecurityTest {

    @Autowired OrderService orderService;

    @Test
    @WithMockUser(roles = "USER")
    void getOwnOrders_succeeds() {
        assertThatNoException().isThrownBy(() -> orderService.getOrdersFor("alice"));
    }

    @Test
    void unauthenticated_throws() {
        assertThatExceptionOfType(AuthenticationCredentialsNotFoundException.class)
            .isThrownBy(() -> orderService.getOrdersFor("alice"));
    }
}
```

### Custom security meta-annotation (reduce repetition)

```java
@Retention(RetentionPolicy.RUNTIME)
@WithMockUser(roles = {"USER", "ADMIN"})
public @interface WithAdminUser {}

// Usage
@Test @WithAdminUser
void adminAction_succeeds() { ... }
```

---

## Assertions

Prefer AssertJ over JUnit assertions — richer failure messages and fluent API:

```java
// Good
assertThat(orders)
    .hasSize(2)
    .extracting(Order::getStatus)
    .containsOnly(Status.PENDING);

assertThatExceptionOfType(ResourceNotFoundException.class)
    .isThrownBy(() -> service.process("bad-id"))
    .withMessageContaining("bad-id");

// Avoid
assertEquals(2, orders.size());
assertThrows(ResourceNotFoundException.class, () -> service.process("bad-id"));
```

---

## Test naming

Use `methodNameScenarioExpectedBehavior`:
add @DisplayName("scenario of the test")
