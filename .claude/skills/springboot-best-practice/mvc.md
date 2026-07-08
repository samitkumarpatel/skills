# Spring MVC Reference

Source: https://docs.spring.io/spring-framework/reference/web/webmvc.html

---

## DispatcherServlet

The central front controller. Spring Boot auto-configures it via `DispatcherServletAutoConfiguration`.

Key beans it delegates to:

| Bean | Role |
|---|---|
| `HandlerMapping` | Maps requests to handlers |
| `HandlerAdapter` | Invokes the matched handler |
| `ViewResolver` | Resolves logical view names to `View` instances |
| `HandlerExceptionResolver` | Handles exceptions from handlers |
| `LocaleResolver` | Resolves locale for i18n |
| `MultipartResolver` | Parses multipart file uploads |
| `FlashMapManager` | Stores/retrieves redirect flash attributes |

---

## Controllers

```java
@Controller          // returns view names / ModelAndView
@RestController      // shorthand for @Controller + @ResponseBody on every method
```

### Request Mapping

```java
@GetMapping("/users/{id}")
@PostMapping("/users")
@PutMapping("/users/{id}")
@DeleteMapping("/users/{id}")
@PatchMapping("/users/{id}")

// Or with explicit method:
@RequestMapping(value = "/users", method = RequestMethod.GET,
                produces = MediaType.APPLICATION_JSON_VALUE)
```

Multiple paths, headers, params, and content-type constraints are all supported on `@RequestMapping`.

---

## Handler Method Parameters

| Annotation | Binds from |
|---|---|
| `@PathVariable` | URI template segment (`/users/{id}`) |
| `@RequestParam` | Query string or form field |
| `@RequestHeader` | HTTP header |
| `@CookieValue` | Cookie |
| `@RequestBody` | Deserialized request body (JSON/XML) |
| `@RequestPart` | Multipart file or part |
| `@ModelAttribute` | Form fields bound to an object |
| `@SessionAttribute` | Existing session attribute (read-only) |
| `@RequestAttribute` | Request-scoped attribute |

Non-annotated parameters:

| Type | Injected automatically |
|---|---|
| `HttpServletRequest` / `HttpServletResponse` | Servlet request/response |
| `HttpSession` | Current session |
| `Principal` | Authenticated principal |
| `Locale` | Resolved locale |
| `BindingResult` | Validation result (must follow `@ModelAttribute` / `@RequestBody`) |

---

## Handler Method Return Types

| Return type | Behaviour |
|---|---|
| `String` | Logical view name |
| `ModelAndView` | View + model data |
| `@ResponseBody` on method | Serialize return value to response body |
| `ResponseEntity<T>` | Full control: status + headers + body |
| `void` | Handled directly via response/output stream |

---

## Request & Response Body

```java
// Deserialize JSON body into object
@PostMapping
public ResponseEntity<User> create(@RequestBody @Valid User user) {
    return ResponseEntity.status(HttpStatus.CREATED).body(service.save(user));
}

// Serialize return value to JSON
@GetMapping("/{id}")
public ResponseEntity<User> get(@PathVariable Long id) {
    return ResponseEntity.ok(service.findById(id));
}
```

Use `ResponseEntity` when you need to set status codes or headers explicitly.

---

## Model & Data Binding

### @ModelAttribute

Populates a model object from request parameters (form posts):

```java
@PostMapping
public String submit(@ModelAttribute @Valid UserForm form, BindingResult result) {
    if (result.hasErrors()) return "form";
    service.save(form);
    return "redirect:/success";
}
```

Place `BindingResult` immediately after the bound argument — Spring requires this order.

### @InitBinder

Per-controller binding customisation (e.g. date formats, disallowed fields):

```java
@InitBinder
public void initBinder(WebDataBinder binder) {
    binder.setDisallowedFields("id");
    binder.registerCustomEditor(LocalDate.class,
        new CustomDateEditor(new SimpleDateFormat("yyyy-MM-dd"), true));
}
```

---

## Validation

```java
@PostMapping
public ResponseEntity<Void> create(@RequestBody @Valid @NotNull UserRequest req,
                                   BindingResult result) {
    if (result.hasErrors()) {
        Map<String, String> errors = result.getFieldErrors().stream()
            .collect(toMap(FieldError::getField, FieldError::getDefaultMessage));
        return ResponseEntity.badRequest().build();
    }
    ...
}
```

Prefer `@ControllerAdvice` + `@ExceptionHandler(MethodArgumentNotValidException.class)` over checking `BindingResult` in every method.

---

## Exception Handling

### Controller-scoped

```java
@ExceptionHandler(EntityNotFoundException.class)
public ResponseEntity<ProblemDetail> handleNotFound(EntityNotFoundException ex) {
    ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    return ResponseEntity.status(HttpStatus.NOT_FOUND).body(pd);
}
```

### Global (@ControllerAdvice)

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetail> handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.UNPROCESSABLE_ENTITY);
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .collect(toMap(FieldError::getField, FieldError::getDefaultMessage)));
        return ResponseEntity.unprocessableEntity().body(pd);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGeneric(Exception ex) {
        return ResponseEntity.internalServerError()
            .body(ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error"));
    }
}
```

Prefer `ProblemDetail` (RFC 9457, available since Spring 6) over custom error DTOs.

more details on exception handling can be found on [exception-handling.md](exception-handling.md) file
---

## Session & Flash Attributes

```java
// Store a model attribute in the HTTP session across requests
@Controller
@SessionAttributes("cart")
public class CheckoutController {
    @ModelAttribute("cart")
    public Cart cart() { return new Cart(); }

    @PostMapping("/checkout")
    public String checkout(@ModelAttribute Cart cart, SessionStatus status) {
        service.process(cart);
        status.setComplete(); // clears session attribute
        return "redirect:/confirmation";
    }
}

// Pass data across a redirect without URL params
@PostMapping
public String save(RedirectAttributes ra) {
    ra.addFlashAttribute("message", "Saved successfully");
    return "redirect:/list";
}
```

---

## CORS

### Per-endpoint

```java
@CrossOrigin(origins = "https://app.example.com", maxAge = 3600)
@RestController
@RequestMapping("/api")
public class ApiController { }
```

### Global

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

---

## Interceptors

```java
public class RequestLoggingInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res,
                             Object handler) {
        log.info("{} {}", req.getMethod(), req.getRequestURI());
        return true; // false = abort request
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                Object handler, Exception ex) {
        log.info("Completed with status {}", res.getStatus());
    }
}

// Registration
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new RequestLoggingInterceptor())
                .addPathPatterns("/api/**");
    }
}
```

---

## Static Resources & View Controllers

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/static/**")
                .addResourceLocations("classpath:/static/")
                .setCacheControl(CacheControl.maxAge(1, TimeUnit.HOURS));
    }

    // No-op controller — just maps a path to a view name
    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/").setViewName("index");
        registry.addRedirectViewController("/home", "/");
    }
}
```

---

## HTTP Message Converters

Spring Boot auto-configures Jackson for JSON. Override only when needed:

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        converters.add(new MappingJackson2HttpMessageConverter(customObjectMapper()));
    }
}
```

Common converters registered by default:

| Converter | Handles |
|---|---|
| `MappingJackson2HttpMessageConverter` | `application/json` |
| `StringHttpMessageConverter` | `text/plain`, `text/*` |
| `ByteArrayHttpMessageConverter` | `application/octet-stream` |
| `ResourceHttpMessageConverter` | `application/octet-stream` (files) |

---

## Async Request Processing

```java
// Offload to thread pool, release servlet thread immediately
@GetMapping("/async")
public Callable<ResponseEntity<Report>> asyncReport() {
    return () -> ResponseEntity.ok(service.generateReport());
}

// Deferred result — set from another thread (e.g. message listener)
@GetMapping("/deferred")
public DeferredResult<ResponseEntity<Data>> deferred() {
    DeferredResult<ResponseEntity<Data>> result = new DeferredResult<>(5000L);
    executor.execute(() -> result.setResult(ResponseEntity.ok(service.fetch())));
    return result;
}
```

---

## HTTP Caching

```java
@GetMapping("/{id}")
public ResponseEntity<User> get(@PathVariable Long id,
                                ShallowEtagHeaderFilter etag,
                                WebRequest request) {
    User user = service.findById(id);
    String etagValue = String.valueOf(user.getVersion());
    if (request.checkNotModified(etagValue)) {
        return ResponseEntity.status(HttpStatus.NOT_MODIFIED).build();
    }
    return ResponseEntity.ok()
        .cacheControl(CacheControl.maxAge(60, TimeUnit.SECONDS))
        .eTag(etagValue)
        .body(user);
}
```

Spring Boot's `ShallowEtagHeaderFilter` can add ETag support automatically via a `FilterRegistrationBean`.

---

## Content Negotiation

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(true)             // ?format=json
            .parameterName("format")
            .ignoreAcceptHeader(false)
            .defaultContentType(MediaType.APPLICATION_JSON)
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML);
    }
}
```

---

## MockMvc Testing

```java
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {

    @Autowired MockMvc mockMvc;
    @Autowired ObjectMapper objectMapper;

    @Test
    void createUser_returns201() throws Exception {
        var body = new CreateUserRequest("alice", "alice@example.com");

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(body)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.email").value("alice@example.com"));
    }

    @Test
    void getUser_notFound_returns404() throws Exception {
        mockMvc.perform(get("/api/users/999"))
            .andExpect(status().isNotFound());
    }
}
```

Use `@WebMvcTest(UserController.class)` to load only the web layer (faster than `@SpringBootTest`).

---

## Common Pitfalls

- **`@EnableWebMvc` in Spring Boot**: disables Boot's auto-configuration. Use `WebMvcConfigurer` beans instead unless you need full manual control.
- **`BindingResult` placement**: must immediately follow the bound argument — placing it elsewhere silently skips validation.
- **`@SessionAttributes` cleanup**: always call `SessionStatus.setComplete()` after the workflow ends to avoid stale session data.
- **CORS vs. Security**: Spring Security's CORS filter runs before MVC. Declare CORS in both `WebMvcConfigurer` and `HttpSecurity.cors()` for secured endpoints; or use `CorsConfigurationSource` in the security config as the single source of truth.
- **`@ControllerAdvice` scope**: by default it applies globally. Narrow it with `assignableTypes`, `annotations`, or `basePackages` to avoid interfering with other modules.
