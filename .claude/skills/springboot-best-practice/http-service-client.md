# HTTP Service Client (Spring Framework 6 / Boot 4)

Spring's `@HttpExchange` interfaces generate declarative HTTP clients with no boilerplate,
replacing manual `RestClient`/`WebClient` wiring.

## Define the interface

```java
public interface MilestoneService {

    @GetExchange("/repos/{org}/{repo}/milestones")
    List<Milestone> getMilestones(@PathVariable String org, @PathVariable String repo);
}
```

Common annotations: `@GetExchange`, `@PostExchange`, `@PutExchange`, `@PatchExchange`, `@DeleteExchange`.

## Wire it up — three approaches

### 1. Manual (single client, pre-Boot 4)

```java
@Bean
MilestoneService milestoneService() {
    RestClient client = RestClient.create("https://api.github.com");
    return HttpServiceProxyFactory.builderFor(RestClientAdapter.create(client))
            .build()
            .createClient(MilestoneService.class);
}
```

### 2. Declarative registry with @ImportHttpServices (Spring Framework 7 / Boot 4)

Eliminates per-bean factory boilerplate. Groups interfaces that share a base URL / client config.

```java
@ImportHttpServices(group = "github",        types = {MilestoneService.class, ReleaseService.class})
@ImportHttpServices(group = "stackoverflow", basePackages = "client.stackoverflow")
@Configuration
public class ClientConfig {}
```

Configure each group's `RestClient` with a `GroupConfigurer` bean:

```java
@Bean
RestClientHttpServiceGroupConfigurer groupConfigurer() {
    return groups -> {
        groups.filterByName("github")
              .forEachClient((_, builder) -> builder.baseUrl("https://api.github.com"));

        groups.filterByName("stackoverflow")
              .forEachClient((_, builder) -> builder.baseUrl("https://api.stackexchange.com?site=stackoverflow"));
    };
}
```

Spring Boot auto-creates beans for every registered interface — inject `MilestoneService` directly.

### 3. Properties-based configuration (Spring Boot 4)

```properties
spring.http.client.service.read-timeout=2s

spring.http.client.service.group.github.base-url=https://api.github.com
spring.http.client.service.group.stackoverflow.base-url=https://api.stackexchange.com
```

Combine with a `@ImportHttpServices` declaration; Boot binds the URL/timeout from properties automatically.

### 4. Programmatic registration (custom filtering logic)

```java
public class CustomHttpServiceRegistrar extends AbstractHttpServiceRegistrar {

    @Override
    protected void registerHttpServices(GroupRegistry registry, AnnotationMetadata metadata) {
        registry.forGroup("github").detectInBasePackages("client.github");
    }
}

@Configuration
@Import(CustomHttpServiceRegistrar.class)
public class ClientConfig {}
```

## Ecosystem integrations

| Feature | Dependency | How |
|---|---|---|
| Load balancing | Spring Cloud 2025.1 | `spring-cloud-starter-loadbalancer` — auto-applied to groups |
| Circuit breaking | Spring Cloud 2025.1 | Resilience4j integration on group configurer |
| OAuth2 | Spring Security 7.0 | `@ClientRegistrationId` annotation on service interface |

## Prefer declarative registry over manual beans

- Fewer `@Bean` methods for each client type
- Base URL in `application.properties` (12-factor friendly)
- One configurer bean handles cross-cutting concerns (timeouts, auth headers) per group
- Spring Boot 4 auto-configuration handles factory lifecycle
