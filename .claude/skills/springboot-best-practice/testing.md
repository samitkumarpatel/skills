# Spring Boot Testing Patterns

References:
- [Spring Framework — Testing](https://docs.spring.io/spring-framework/reference/testing.html)
- [Spring Boot — Testing](https://docs.spring.io/spring-boot/reference/testing/index.html)
- [Spring Security — Test](https://docs.spring.io/spring-security/reference/servlet/test/index.html)

---

## Test layers — use the right slice

| What you're testing | Annotation | Loads | Test client |
|---|---|---|---|
| Controller (MVC layer only) | `@WebMvcTest(MyController.class)` | MVC infra + security | `MockMvc` / `MockMvcTester` |
| JSON serialization | `@JsonTest` | Jackson mapper only | `JacksonTester` |
| Repository (JPA) | `@DataJpaTest` | JPA + embedded DB | — |
| REST client (`@HttpExchange`) | `@RestClientTest(MyClient.class)` | RestClient wiring only | — |
| Full context, no server | `@SpringBootTest` + `@AutoConfigureMockMvc` | Full context, mock web env | `MockMvc` / `MockMvcTester` |
| Full context, real server | `@SpringBootTest(webEnvironment = RANDOM_PORT)` | Full context, real HTTP | `RestTestClient` / `TestRestTemplate` |
| Pure logic | none (plain JUnit) | Nothing | — |

Avoid `@SpringBootTest` for unit tests — it is slow. Prefer slices or plain JUnit.

---

## MockMvc vs RestTestClient — when to use which

| | `MockMvc` / `MockMvcTester` | `RestTestClient` | `TestRestTemplate` |
|---|---|---|---|
| Web environment | `MOCK` (no server) | `RANDOM_PORT` (real server) | `RANDOM_PORT` (real server) |
| Protocol | In-process, no TCP | Real HTTP over TCP | Real HTTP over TCP |
| Speed | Fastest | Slower (server startup) | Slower (server startup) |
| Security filters | Applied when `springSecurity()` is used | Always applied (real filter chain) | Always applied |
| AssertJ API | `MockMvcTester` (preferred) | Yes (fluent) | No (plain assertions) |
| Reactive support | No | No (blocking) | No |
| Best for | Controller unit tests, slice tests | True end-to-end integration tests | Legacy; prefer `RestTestClient` |

**Rule of thumb:**
- Use `MockMvc` / `MockMvcTester` with `@WebMvcTest` or `@SpringBootTest + @AutoConfigureMockMvc` for the vast majority of controller tests — fast and precise.
- Use `RestTestClient` with `RANDOM_PORT` only when you need real HTTP (e.g., testing filters, interceptors, or TLS behaviour that can't be exercised in-process).

---

## @WebMvcTest — controller slice

Loads only the MVC layer. Use `@MockitoBean` to stub service dependencies.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvcTester mvc;
    @MockitoBean OrderService orderService;

    @Test
    void createOrder_returns201() {
        given(orderService.create(any())).willReturn(new OrderResponse("ord-1", "PENDING"));

        assertThat(mvc.post().uri("/orders")
                .contentType(APPLICATION_JSON)
                .content("""{"customerId":"cust-1","items":[],"totalAmount":10}"""))
            .hasStatus(HttpStatus.CREATED)
            .hasHeader("Location");
    }

    @Test
    void createOrder_invalidBody_returns422() {
        assertThat(mvc.post().uri("/orders")
                .contentType(APPLICATION_JSON)
                .content("{}"))
            .hasStatus(HttpStatus.UNPROCESSABLE_ENTITY)
            .bodyJson().extractingPath("$.title").isEqualTo("Validation Failed");
    }
}
```

### @WebMvcTest with Spring Security

`@WebMvcTest` loads the security filter chain. Always configure `springSecurity()` and supply authentication on each request:

```java
@WebMvcTest(OrderController.class)
class OrderControllerSecurityTest {

    @Autowired WebApplicationContext context;
    @MockitoBean OrderService orderService;

    MockMvc mockMvc;

    @BeforeEach
    void setup() {
        mockMvc = MockMvcBuilders
            .webAppContextSetup(context)
            .apply(springSecurity())          // wires Spring Security filters into MockMvc
            .build();
    }

    @Test
    void unauthenticated_returns401() throws Exception {
        mockMvc.perform(get("/orders"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(roles = "USER")             // annotation approach
    void authenticatedUser_returns200() throws Exception {
        mockMvc.perform(get("/orders"))
            .andExpect(status().isOk());
    }

    @Test
    void adminEndpoint_withoutRole_returns403() throws Exception {
        mockMvc.perform(get("/admin").with(user("alice").roles("USER")))
            .andExpect(status().isForbidden());
    }

    @Test
    void adminEndpoint_withRole_returns200() throws Exception {
        mockMvc.perform(get("/admin").with(user("alice").roles("ADMIN")))
            .andExpect(status().isOk());
    }
}
```

### @WebMvcTest with JWT / OAuth2 Resource Server

```java
@WebMvcTest(OrderController.class)
class OrderControllerJwtTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;

    @Test
    void noToken_returns401() throws Exception {
        mockMvc.perform(get("/orders"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void validJwt_returns200() throws Exception {
        mockMvc.perform(get("/orders").with(jwt()))
            .andExpect(status().isOk());
    }

    @Test
    void jwtWithClaims_returns200() throws Exception {
        mockMvc.perform(get("/orders")
                .with(jwt()
                    .jwt(j -> j.claim("sub", "alice").claim("scope", "orders:read"))
                    .authorities(new SimpleGrantedAuthority("SCOPE_orders:read"))))
            .andExpect(status().isOk());
    }

    @Test
    void oidcLogin_returns200() throws Exception {
        mockMvc.perform(get("/me")
                .with(oidcLogin()
                    .idToken(t -> t.claim("email", "alice@example.com"))))
            .andExpect(status().isOk());
    }

    @Test
    void opaqueToken_returns200() throws Exception {
        mockMvc.perform(get("/orders")
                .with(opaqueToken()
                    .authorities(new SimpleGrantedAuthority("SCOPE_orders:read"))))
            .andExpect(status().isOk());
    }
}
```

### Security annotations on class (apply to all methods)

```java
@WebMvcTest(OrderController.class)
@WithMockUser(roles = "USER")        // default user for every test in this class
class OrderControllerTest {

    @Test
    void listOrders_returns200() throws Exception { ... }  // runs as USER

    @Test
    @WithMockUser(roles = "ADMIN")   // overrides class-level annotation
    void deleteOrder_asAdmin_returns204() throws Exception { ... }

    @Test
    @WithAnonymousUser               // overrides to anonymous
    void publicEndpoint_returns200() throws Exception { ... }
}
```

---

## @SpringBootTest with MockMvc (full context, no server)

Use when you need the full application context (e.g., real service + repository wiring) but still want in-process request testing:

```java
@SpringBootTest
@AutoConfigureMockMvc
class OrderIntegrationTest {

    @Autowired MockMvcTester mvc;

    @Test
    @WithMockUser(roles = "USER")
    void createAndFetchOrder() {
        assertThat(mvc.post().uri("/orders")
                .contentType(APPLICATION_JSON)
                .content("""{"customerId":"cust-1","items":[],"totalAmount":10}"""))
            .hasStatus(HttpStatus.CREATED);
    }
}
```

Security is fully applied (real filter chain). Use `@WithMockUser`, `jwt()`, or `oauth2Login()` exactly as in `@WebMvcTest`.

---

## @SpringBootTest with real server (RANDOM_PORT)

Use for true end-to-end tests that must go through real HTTP:

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
class OrderE2ETest {

    @Autowired RestTestClient restClient;

    @Test
    void createOrder_returnsCreated() {
        restClient.post().uri("/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""{"customerId":"cust-1","items":[],"totalAmount":10}""")
            .exchange()
            .expectStatus().isCreated()
            .expectHeader().exists("Location");
    }
}
```

> Security filters run against real HTTP here — configure a real token or disable security in the test profile. `@WithMockUser` and `jwt()` post-processors **do not work** with `RANDOM_PORT`; use `TestRestTemplate` with an `Authorization` header, or set `spring.security.test.context.support.ReactorContextTestExecutionListener` + actual token setup.

---

## Service unit tests

No Spring context — instantiate directly. Always fastest:

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

### Testing @PreAuthorize on service methods

```java
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

    @Test
    @WithMockUser(roles = "USER")
    void getOtherUsersOrders_throwsAccessDenied() {
        assertThatExceptionOfType(AccessDeniedException.class)
            .isThrownBy(() -> orderService.getOrdersFor("bob"));
    }
}
```

---

## @DataJpaTest — repository slice

Uses an embedded H2 database by default. `@Transactional` rolls back after each test automatically:

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

To use the real database instead of H2:

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)
class OrderRepositoryRealDbTest { ... }
```

---

## Integration tests with Testcontainers

Use for tests that need a real database, broker, or external service:

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

## Bean overriding

### @MockitoBean — replace with a Mockito mock

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @MockitoBean OrderService orderService;  // all methods return null/empty by default
}
```

### @MockitoSpyBean — wrap real bean, selectively stub

```java
@SpringBootTest
class PartialOverrideTest {
    @MockitoSpyBean OrderService orderService;

    @Test
    void realBehaviorWithOneStubbed() {
        doReturn(List.of()).when(orderService).getPendingOrders();
    }
}
```

### @TestBean — hand-crafted test double (no Mockito)

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

## Transaction handling in tests

`@Transactional` on a test rolls back automatically after each test:

```java
@SpringBootTest
@Transactional
class OrderTransactionalTest {

    @Autowired OrderRepository repository;

    @Test
    void saveOrder_persists() {
        repository.save(new Order(null, "cust-1", Status.PENDING));
        assertThat(repository.count()).isEqualTo(1);
    }   // rolled back — next test starts clean
}
```

Use `@BeforeTransaction` / `@AfterTransaction` for setup/teardown that must run outside the transaction:

```java
@BeforeTransaction
void insertBaseData() { /* insert reference data that must be committed */ }

@AfterTransaction
void cleanUp() { /* delete outside the test transaction */ }
```

> `@Transactional` rollback does **not** work with `RANDOM_PORT` — the test and the server run in different threads. Use Testcontainers + explicit cleanup instead.

---

## Property overrides

```java
@SpringBootTest
@TestPropertySource(properties = {
    "app.payment.api-url=http://localhost:9090",
    "app.payment.timeout-seconds=1"
})
class PaymentServiceTest { ... }
```

Or in `@SpringBootTest` directly:

```java
@SpringBootTest(properties = "spring.main.web-application-type=reactive")
```

---

## SQL script setup with @Sql

```java
@SpringBootTest
@Transactional
@Sql("/test-data/orders.sql")
@Sql(scripts = "/test-data/cleanup.sql", executionPhase = AFTER_TEST_METHOD)
class OrderQueryTest { ... }
```

---

## Context caching

Spring caches the `ApplicationContext` across tests that share identical configuration. A new context loads only when config differs (different beans, profiles, properties).

- Group tests that share context config into the same class or a common base
- Use `@ActiveProfiles` consistently — mixing profiles creates multiple cached contexts
- Use `@DirtiesContext` sparingly — it forces a full reload

```java
@DirtiesContext(classMode = ClassMode.AFTER_EACH_TEST_METHOD)
class StatefulBeanTest { ... }
```

---

## Security testing — quick reference

| Scenario | Mechanism | Works with |
|---|---|---|
| Simple authenticated user | `@WithMockUser` / `.with(user("alice"))` | MockMvc |
| Specific role | `@WithMockUser(roles="ADMIN")` / `.with(user("x").roles("ADMIN"))` | MockMvc |
| Anonymous user | `@WithAnonymousUser` / `.with(anonymous())` | MockMvc |
| JWT resource server | `.with(jwt().jwt(j -> j.claim("sub","alice")))` | MockMvc |
| OIDC login | `.with(oidcLogin().idToken(t -> t.claim("email","a@b.com")))` | MockMvc |
| OAuth2 login | `.with(oauth2Login().attributes(a -> a.put("sub","alice")))` | MockMvc |
| Opaque token | `.with(opaqueToken())` | MockMvc |
| @PreAuthorize on service | `@WithMockUser` on the test method + `@SpringBootTest` | Full context |
| Custom reusable user | Static factory: `user("rob").roles("ADMIN")` | MockMvc |
| Class-level default | `@WithMockUser` on the test class | MockMvc |

---

## Spring Modulith — module integration testing

Reference: [Spring Modulith — Testing](https://docs.spring.io/spring-modulith/reference/testing.html)

Add the test starter:

```xml
<dependency>
  <groupId>org.springframework.modulith</groupId>
  <artifactId>spring-modulith-starter-test</artifactId>
  <scope>test</scope>
</dependency>
```

### @ApplicationModuleTest — bootstrap modes

`@ApplicationModuleTest` bootstraps only the beans that belong to the module under test (derived from the test's package). Choose how much of the dependency graph to include:

| Mode | What is loaded |
|---|---|
| `STANDALONE` (default) | Current module only — mock everything else |
| `DIRECT_DEPENDENCIES` | Current module + directly referenced modules |
| `ALL_DEPENDENCIES` | Current module + full transitive dependency tree |

```java
package example.order;

@ApplicationModuleTest                                      // STANDALONE
class OrderModuleTest { ... }

@ApplicationModuleTest(mode = BootstrapMode.DIRECT_DEPENDENCIES)
class OrderWithInventoryTest { ... }

@ApplicationModuleTest(mode = BootstrapMode.ALL_DEPENDENCIES)
class OrderFullTest { ... }
```

Mock beans from other modules that are not bootstrapped:

```java
@ApplicationModuleTest
class InventoryModuleTest {

    @MockitoBean SomeOtherModuleService otherService;
}
```

### Verifying event publication with PublishedEvents

Inject `PublishedEvents` or `AssertablePublishedEvents` as a test method parameter:

```java
@ApplicationModuleTest
class OrderModuleTest {

    @Test
    void completingOrderPublishesEvent(PublishedEvents events) {
        // ... trigger order completion

        var published = events.ofType(OrderCompleted.class)
            .matching(OrderCompleted::getOrderId, "ord-1");

        assertThat(published).hasSize(1);
    }
}
```

With `AssertablePublishedEvents` for fluent AssertJ style:

```java
@Test
void completingOrderPublishesEvent(AssertablePublishedEvents events) {
    // ... trigger order completion

    assertThat(events)
        .contains(OrderCompleted.class)
        .matching(OrderCompleted::getOrderId, "ord-1");
}
```

### Scenario API — testing async event flows

The `Scenario` API handles the timing of asynchronous `@ApplicationModuleListener` calls — no manual `Thread.sleep` or `Awaitility` setup needed.

**Stimulus → expect event:**

```java
@ApplicationModuleTest
class InventoryModuleTest {

    @Test
    void orderCompletionReducesStock(Scenario scenario) {
        scenario
            .publish(new OrderCompleted("ord-1"))
            .andWaitForEventOfType(StockUpdated.class)
            .matching(e -> e.orderId().equals("ord-1"))
            .toArriveAndVerify(e -> assertThat(e.quantity()).isEqualTo(0));
    }
}
```

**Stimulus → expect state change:**

```java
@Test
void orderCompletionUpdatesInventory(Scenario scenario) {
    scenario
        .publish(new OrderCompleted("ord-1"))
        .andWaitForStateChange(() -> inventoryRepository.findByOrderId("ord-1"))
        .andVerify(result -> assertThat(result).isPresent());
}
```

**Stimulus via bean invocation:**

```java
@Test
void processingOrderPublishesEvent(Scenario scenario) {
    scenario
        .stimulate(() -> orderService.complete(new Order("ord-1")))
        .andWaitForEventOfType(OrderCompleted.class)
        .toArrive();
}
```

**Customise timeout per scenario:**

```java
scenario
    .publish(new OrderCompleted("ord-1"))
    .customize(cf -> cf.atMost(Duration.ofSeconds(2)))
    .andWaitForEventOfType(StockUpdated.class)
    .toArrive();
```

### Module slice testing with @DataJpaTest

Combine vertical module slicing with horizontal slice annotations using `@ModuleSlicing`:

```java
package example.order;

@ModuleSlicing
@DataJpaTest
class OrderRepositoryTest {

    @Autowired OrderRepository repository;

    @Test
    void savesOrder() { ... }
}
```

### Change-aware test execution (skip unaffected tests)

Add `spring-modulith-junit` to skip module tests that are unaffected by source changes — useful in CI:

```xml
<dependency>
  <groupId>org.springframework.modulith</groupId>
  <artifactId>spring-modulith-junit</artifactId>
  <scope>test</scope>
</dependency>
```

```yaml
# application-test.yml
spring:
  modulith:
    test:
      on-no-changes: skip-all          # skip everything when nothing changed
      reference-commit: ${GIT_COMMIT}  # compare against this commit in CI
```

---

## Assertions

Prefer AssertJ over JUnit assertions:

```java
assertThat(orders)
    .hasSize(2)
    .extracting(Order::getStatus)
    .containsOnly(Status.PENDING);

assertThatExceptionOfType(ResourceNotFoundException.class)
    .isThrownBy(() -> service.process("bad-id"))
    .withMessageContaining("bad-id");
```

## Test naming

Use `methodName_scenario_expectedBehavior` and add `@DisplayName("human readable description")`.
