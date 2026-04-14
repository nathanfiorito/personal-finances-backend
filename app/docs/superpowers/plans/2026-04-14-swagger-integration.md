# Swagger Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Swagger UI with JWT Bearer authentication to the Spring Boot backend, controllable via the `SWAGGER_ENABLED` environment variable.

**Architecture:** springdoc-openapi 2.x is added as a dependency and auto-configures the Swagger UI at `/swagger-ui/index.html` and the OpenAPI spec at `/v3/api-docs`. A new `OpenApiConfig` bean declares the Bearer JWT security scheme globally. `SecurityConfig` is updated to allow unauthenticated access to the Swagger paths (the JWT auth happens inside the UI itself). Swagger is disabled by default via `application.properties` and enabled by setting `SWAGGER_ENABLED=true`.

**Tech Stack:** Spring Boot 3.4.5, springdoc-openapi-starter-webmvc-ui 2.8.5, JJWT 0.12.6, JUnit 5 + AssertJ + MockMvc.

---

## File Map

| File | Action |
|---|---|
| `app/pom.xml` | Add `springdoc-openapi-starter-webmvc-ui` dependency |
| `app/src/main/resources/application.properties` | Add two `springdoc.*` properties |
| `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/config/OpenApiConfig.java` | Create — `@OpenAPIDefinition` + `@SecurityScheme` |
| `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/security/SecurityConfig.java` | Update `permitAll()` to include Swagger paths |
| `app/src/test/java/br/com/nathanfiorito/finances/interfaces/rest/swagger/SwaggerSecurityIT.java` | Create — verifies Swagger paths are not blocked by Spring Security |

---

## Task 1: Add springdoc-openapi dependency

**Files:**
- Modify: `app/pom.xml`

- [ ] **Step 1: Add dependency**

In `app/pom.xml`, inside `<dependencies>`, add after the last `<dependency>` block:

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.5</version>
</dependency>
```

- [ ] **Step 2: Verify the dependency resolves**

```bash
cd app && mvn dependency:resolve -q
```

Expected: BUILD SUCCESS, no errors. If version 2.8.5 is unavailable, use the latest 2.x from [Maven Central](https://central.sonatype.com/artifact/org.springdoc/springdoc-openapi-starter-webmvc-ui).

- [ ] **Step 3: Commit**

```bash
git add app/pom.xml
git commit -m "chore: add springdoc-openapi dependency"
```

---

## Task 2: Add springdoc properties to application.properties

**Files:**
- Modify: `app/src/main/resources/application.properties`

- [ ] **Step 1: Add properties**

At the end of `application.properties`, add:

```properties
springdoc.swagger-ui.enabled=${SWAGGER_ENABLED:false}
springdoc.api-docs.enabled=${SWAGGER_ENABLED:false}
```

- [ ] **Step 2: Commit**

```bash
git add app/src/main/resources/application.properties
git commit -m "chore: disable swagger by default, enable via SWAGGER_ENABLED env var"
```

---

## Task 3: Write failing security integration test

**Files:**
- Create: `app/src/test/java/br/com/nathanfiorito/finances/interfaces/rest/swagger/SwaggerSecurityIT.java`

The goal of this test is to verify that the Swagger paths (`/v3/api-docs`, `/swagger-ui/index.html`) pass through Spring Security without requiring a JWT. Before fixing `SecurityConfig`, these paths fall into `anyRequest().authenticated()` and return HTTP 401. After the fix, they are permitted and return HTTP 404 (no handler registered in this test slice — that is expected and correct).

- [ ] **Step 1: Create the test class**

```java
package br.com.nathanfiorito.finances.interfaces.rest.swagger;

import br.com.nathanfiorito.finances.interfaces.rest.auth.AuthController;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

@WebMvcTest(AuthController.class)
class SwaggerSecurityIT extends BaseControllerIT {

    @Test
    void apiDocsShouldNotRequireAuthentication() throws Exception {
        var result = mockMvc.perform(get("/v3/api-docs")).andReturn();
        assertThat(result.getResponse().getStatus()).isNotEqualTo(401);
    }

    @Test
    void swaggerUiShouldNotRequireAuthentication() throws Exception {
        var result = mockMvc.perform(get("/swagger-ui/index.html")).andReturn();
        assertThat(result.getResponse().getStatus()).isNotEqualTo(401);
    }
}
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd app && mvn test -pl . -Dtest=SwaggerSecurityIT -q
```

Expected: 2 tests FAIL — both paths currently return HTTP 401 because `SecurityConfig` has `anyRequest().authenticated()` and no explicit `permitAll()` for Swagger paths.

---

## Task 4: Create OpenApiConfig

**Files:**
- Create: `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/config/OpenApiConfig.java`

- [ ] **Step 1: Create the file**

```java
package br.com.nathanfiorito.finances.infrastructure.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeIn;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springframework.context.annotation.Configuration;

@Configuration
@OpenAPIDefinition(
    info = @Info(
        title = "Personal Finances API",
        version = "v1",
        description = "REST API for the personal expense tracker"
    ),
    security = @SecurityRequirement(name = "bearerAuth")
)
@SecurityScheme(
    name = "bearerAuth",
    type = SecuritySchemeType.HTTP,
    scheme = "bearer",
    bearerFormat = "JWT",
    in = SecuritySchemeIn.HEADER
)
public class OpenApiConfig {
}
```

---

## Task 5: Update SecurityConfig to permit Swagger paths

**Files:**
- Modify: `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/security/SecurityConfig.java`

- [ ] **Step 1: Add Swagger paths to permitAll()**

Replace the `authorizeHttpRequests` block in `SecurityConfig.filterChain()`:

```java
.authorizeHttpRequests(auth -> auth
    .requestMatchers("/api/auth/**").permitAll()
    .requestMatchers("/webhook").permitAll()
    .requestMatchers(
        "/swagger-ui/**",
        "/swagger-ui.html",
        "/v3/api-docs/**"
    ).permitAll()
    .anyRequest().authenticated()
)
```

- [ ] **Step 2: Run the tests to confirm they now pass**

```bash
cd app && mvn test -pl . -Dtest=SwaggerSecurityIT -q
```

Expected: 2 tests PASS — both paths now return HTTP 404 (permitted by security, no handler in this test slice) instead of 401.

- [ ] **Step 3: Run the full unit test suite to confirm no regressions**

```bash
cd app && mvn test -q
```

Expected: BUILD SUCCESS, all tests pass.

- [ ] **Step 4: Commit**

```bash
git add \
  app/src/main/java/br/com/nathanfiorito/finances/infrastructure/config/OpenApiConfig.java \
  app/src/main/java/br/com/nathanfiorito/finances/infrastructure/security/SecurityConfig.java \
  app/src/test/java/br/com/nathanfiorito/finances/interfaces/rest/swagger/SwaggerSecurityIT.java
git commit -m "feat: add Swagger UI with JWT Bearer auth, disabled by default"
```

---

## Task 6: Smoke test locally

- [ ] **Step 1: Start the dev server with Swagger enabled**

```bash
cd app && SWAGGER_ENABLED=true mvn spring-boot:run
```

- [ ] **Step 2: Verify Swagger UI loads**

Open `http://localhost:8080/swagger-ui/index.html` in your browser.

Expected: Swagger UI renders with an "Authorize" button in the top-right corner. All API groups (transactions, categories, reports, auth) appear as collapsible sections.

- [ ] **Step 3: Verify JWT authentication works end-to-end**

1. Expand `POST /api/auth/login` → click "Try it out" → enter `{"email": "<your-admin-email>", "password": "<your-admin-password>"}` → Execute.
2. Copy the `token` value from the response body.
3. Click the **"Authorize"** button at the top → paste the token in the `bearerAuth` field → click "Authorize" → "Close".
4. Try any protected endpoint (e.g., `GET /api/v1/transactions`) → Execute.

Expected: protected endpoints return data (not 401).

- [ ] **Step 4: Verify Swagger is disabled without the env var**

```bash
cd app && mvn spring-boot:run
```

Open `http://localhost:8080/swagger-ui/index.html`.

Expected: HTTP 404 — Swagger UI is not served.

- [ ] **Step 5: Final commit if smoke test required any fixes**

If no fixes were needed, there is nothing to commit. If fixes were needed, commit them:

```bash
git add <fixed-files>
git commit -m "fix: <describe what was adjusted>"
```
