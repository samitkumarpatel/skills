# Spring Boot Exception Handling

Reference: [Spring MVC — @ExceptionHandler](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html)

## Custom exceptions

Define domain exceptions in the `exception/` package:

```java
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}

public class ConflictException extends RuntimeException {
    public ConflictException(String message) {
        super(message);
    }
}
```

## @ExceptionHandler scope — local vs global

`@ExceptionHandler` can be declared in two scopes:

**Local** — inside a `@Controller` or `@RestController`, applies only to that controller:

```java
@RestController
public class OrderController {

    @ExceptionHandler(IOException.class)
    ResponseEntity<String> handleIo(IOException ex) {
        return ResponseEntity.internalServerError().body("Could not read file storage");
    }
}
```

**Global** — inside `@ControllerAdvice`, applies across all controllers. Prefer this for domain exceptions:

```java
@ControllerAdvice
public class GlobalExceptionHandler { ... }
```

## @ControllerAdvice with ProblemDetail (RFC 9457, Spring 6+)

```java
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    ProblemDetail handleNotFound(ResourceNotFoundException ex) {
        var pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Resource Not Found");
        return pd;
    }

    @ExceptionHandler(ConflictException.class)
    ProblemDetail handleConflict(ConflictException ex) {
        var pd = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        pd.setTitle("Conflict");
        return pd;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        var pd = ProblemDetail.forStatus(HttpStatus.UNPROCESSABLE_ENTITY);
        pd.setTitle("Validation Failed");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .toList());
        return pd;
    }

    @ExceptionHandler(Exception.class)
    ProblemDetail handleGeneric(Exception ex) {
        var pd = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        pd.setTitle("Internal Server Error");
        return pd;
    }
}
```

## Enable RFC 9457 response format

```yaml
spring:
  mvc:
    problemdetails:
      enabled: true
```

## Handling multiple exception types in one method

```java
@ExceptionHandler({FileSystemException.class, RemoteException.class})
ResponseEntity<String> handleStorageExceptions(IOException ex) {
    return ResponseEntity.internalServerError().body(ex.getMessage());
}
```

Prefer individual `@ExceptionHandler` methods per exception type when the response body or status differs — it keeps each handler focused and avoids type-check branching inside the method.

## Exception cause chain matching

Spring matches exceptions at any depth in the cause chain (as of Spring 5.3). Root exception matches take priority over nested cause matches — `ExceptionDepthComparator` ranks them by depth from the thrown type. An unmatched handler can rethrow the exception to continue resolution through the chain.

## Media type mapping (content negotiation)

Declare `produces` to return different error formats based on the client's `Accept` header:

```java
@ExceptionHandler(value = IllegalArgumentException.class, produces = "application/json")
ResponseEntity<ProblemDetail> handleJson(IllegalArgumentException ex) {
    return ResponseEntity.badRequest().body(
        ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, ex.getMessage()));
}

@ExceptionHandler(value = IllegalArgumentException.class, produces = "text/html")
String handleHtml(IllegalArgumentException ex, Model model) {
    model.addAttribute("error", ex.getMessage());
    return "errorView";
}
```

## Supported method arguments

| Argument | Use case |
|---|---|
| Exception type | Access the raised exception |
| `HandlerMethod` | Inspect the controller method that triggered the exception |
| `WebRequest` / `NativeWebRequest` | Request parameters and attributes without Servlet API |
| `HttpServletRequest` / `HttpServletResponse` | Raw Servlet request/response |
| `HttpMethod` | HTTP method of the request |
| `java.security.Principal` | Currently authenticated user |
| `Locale` | Current request locale (via `LocaleResolver`) |
| `OutputStream` / `Writer` | Write directly to the response body |
| `@RequestAttribute` / `@SessionAttribute` | Access request or session attributes |

## Supported return types

| Return type | Behaviour |
|---|---|
| `ResponseEntity<B>` | Full response — status, headers, and body via `HttpMessageConverter` |
| `ProblemDetail` / `ErrorResponse` | RFC 9457 response — preferred for REST APIs |
| `String` | View name resolved by `ViewResolver` |
| `ModelAndView` | View + model attributes |
| `void` | Response already written (e.g. via `OutputStream` argument) |

## Do not

- Catch-and-swallow exceptions silently
- Expose stack traces or internal details in production error responses
- Catch `Exception` inside service methods — let it propagate to the `@ControllerAdvice` layer
- Throw exceptions from repositories — propagate to the advice layer
- Add multiple exception types to one handler when their responses differ — use separate methods instead
