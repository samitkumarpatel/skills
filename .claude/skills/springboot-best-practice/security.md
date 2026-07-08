# Spring Boot Security Patterns

## SecurityFilterChain — always use the bean approach (Spring Security 6+)

Reference: [Spring Security — Java Configuration](https://docs.spring.io/spring-security/reference/servlet/configuration/java.html#modular-httpsecurity-configuration)

Never extend `WebSecurityConfigurerAdapter` (removed in Spring Security 6). Declare a `SecurityFilterChain` bean instead:

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity          // enables @PreAuthorize on methods
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)            // stateless API — no CSRF needed
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health", "/auth/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .build();
    }
}
```

## Modular configuration with Customizer beans (Spring Security 7+)

For small cross-cutting concerns, declare `Customizer<HttpSecurity>` beans instead of overriding the whole `SecurityFilterChain`. They are auto-applied to every `HttpSecurity` instance before the chain is built:

```java
@Bean
ThrowingCustomizer<HttpSecurity> httpsRedirect() {
    return http -> http.redirectToHttps(Customizer.withDefaults());
}
```

For sub-configurer types, declare a `Customizer<T>` where `T` is a sub-configurer argument (e.g. `HeadersConfigurer`):

```java
@Bean
Customizer<HeadersConfigurer<HttpSecurity>> contentSecurityPolicy() {
    return headers -> headers
        .contentSecurityPolicy(csp -> csp.policyDirectives("object-src 'none'"));
}
```

Use `@Order` when multiple `Customizer<HttpSecurity>` beans must run in a defined sequence:

```java
@Bean
@Order(Ordered.HIGHEST_PRECEDENCE)
ThrowingCustomizer<HttpSecurity> adminAuthorization() {
    return http -> http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/admin/**").hasRole("ADMIN"));
}
```

## Multiple SecurityFilterChain beans

Use multiple chains with `@Order` and `securityMatcher` to apply different policies per URL pattern:

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    @Order(1)                           // evaluated first
    SecurityFilterChain apiFilterChain(HttpSecurity http) throws Exception {
        return http
            .securityMatcher("/api/**") // this chain only handles /api/**
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth.anyRequest().hasRole("ADMIN"))
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .build();
    }

    @Bean                               // fallback — no securityMatcher, catches the rest
    SecurityFilterChain defaultFilterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated())
            .formLogin(Customizer.withDefaults())
            .build();
    }
}
```

### securityMatcher vs requestMatchers

| | `securityMatcher` | `requestMatchers` |
|---|---|---|
| Scope | Filter chain level — determines whether this chain handles the request at all | Authorization level — rules within a chain |
| Default | Matches every request | N/A |
| Miss behaviour | Request falls through to the next chain | N/A |

> Requests that don't match any `securityMatcher` are **not protected**. Always provide a fallback chain with no `securityMatcher` as the last `@Order`.

## JWT — use Spring's OAuth2 resource server, not manual parsing

Add `spring-boot-starter-oauth2-resource-server` and configure the JWKS URI:

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          jwk-set-uri: ${AUTH_SERVER_JWKS_URI}
```

Access claims in controllers:

```java
@GetMapping("/me")
ResponseEntity<UserInfo> me(@AuthenticationPrincipal Jwt jwt) {
    return ResponseEntity.ok(new UserInfo(
        jwt.getSubject(),
        jwt.getClaimAsStringList("roles")
    ));
}
```

## Method-level security

Prefer `@PreAuthorize` on service methods over URL rules for business logic:

```java
@Service
public class OrderService {

    @PreAuthorize("hasRole('ADMIN') or #customerId == authentication.name")
    public List<Order> getOrdersFor(String customerId) { ... }

    @PreAuthorize("hasRole('ADMIN')")
    public void deleteOrder(String id) { ... }
}
```

## CORS

Configure centrally, not per-controller:

```java
@Bean
CorsConfigurationSource corsConfigurationSource() {
    var config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://app.example.com"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE"));
    config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
    config.setAllowCredentials(true);

    var source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", config);
    return source;
}
```

## Security testing

For complete security testing patterns — `springSecurity()` MockMvc setup, `@WithMockUser`, JWT/OAuth2 mocks (`jwt()`, `oauth2Login()`, `oidcLogin()`), and `@PreAuthorize` service tests — see [testing.md](testing.md#spring-security-testing).

## Do not

- Store secrets in `application.yml` — use environment variables or a secrets manager
- Log authentication tokens or full request bodies containing credentials
- Use `permitAll()` as a catch-all — default to `anyRequest().authenticated()`
- Use HTTP Basic in production REST APIs
