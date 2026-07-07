# Spring Boot Security Patterns

## SecurityFilterChain — always use the bean approach (Spring Security 6+)

Never extend `WebSecurityConfigurerAdapter` (removed in Spring Security 6).

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
