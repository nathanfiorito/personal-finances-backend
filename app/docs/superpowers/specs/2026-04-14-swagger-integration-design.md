# Swagger / OpenAPI Integration Design

**Date:** 2026-04-14
**Branch:** feature/swagger-integration
**Status:** Approved

---

## Overview

Add Swagger UI (via springdoc-openapi) to the personal-finances backend. The UI exposes all REST endpoints with interactive documentation and supports JWT Bearer authentication so the user can obtain a token via `/api/auth/login` and authorize subsequent calls directly in the browser.

Swagger is disabled by default and enabled in production via the `SWAGGER_ENABLED` environment variable.

---

## Components

### 1. `pom.xml` — new dependency

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.5</version>
</dependency>
```

springdoc-openapi 2.x is the actively maintained version for Spring Boot 3.x.

### 2. `infrastructure/config/OpenApiConfig.java` — new file

Responsibilities:
- `@OpenAPIDefinition` — sets title ("Personal Finances API"), version (`v1`), and a global `@SecurityRequirement` named `bearerAuth` so every endpoint shows the lock icon automatically.
- `@SecurityScheme` — declares the `bearerAuth` scheme (type HTTP, scheme `bearer`, bearerFormat `JWT`). This renders the "Authorize" button in the Swagger UI where the user pastes their JWT.

The `/api/auth/login` endpoint does not require a security requirement annotation — the springdoc global security requirement applies only to routes that also have `@Tag` or are included by default; the `SecurityConfig.permitAll()` on `/api/auth/**` is sufficient context. If the lock icon appears on the login route, `@SecurityRequirements({})` can be added to `AuthController` to suppress it.

### 3. `infrastructure/security/SecurityConfig.java` — updated

Add to the `permitAll()` block:
- `/swagger-ui/**`
- `/swagger-ui.html`
- `/v3/api-docs/**`

These paths must be open so the browser can load the Swagger UI assets and the OpenAPI JSON spec without a JWT. Authentication happens inside the UI (the "Authorize" button).

### 4. `application.properties` — two new properties

```properties
springdoc.swagger-ui.enabled=${SWAGGER_ENABLED:false}
springdoc.api-docs.enabled=${SWAGGER_ENABLED:false}
```

- Both default to `false`. Neither the UI nor the raw OpenAPI spec (`/v3/api-docs`) are accessible without the env var.
- To enable: set `SWAGGER_ENABLED=true` in the VPS environment.
- Both properties must be set together: disabling only the UI would still expose the spec JSON at `/v3/api-docs`.

---

## Data flow — authenticating in Swagger UI

1. User opens `http://<vps-ip>:8080/swagger-ui/index.html` in their browser.
2. Clicks **"Authorize"** → enters email + password in the `POST /api/auth/login` endpoint → executes → copies the JWT from the response.
3. Clicks **"Authorize"** again → pastes `<token>` in the Bearer field → confirms.
4. All subsequent Swagger UI calls include `Authorization: Bearer <token>` automatically.

> CORS note: because the Swagger UI page is served from the same host and port as the API, all browser requests are same-origin and CORS does not apply — regardless of the physical machine the browser runs on.

---

## Error handling

No new error handling required. springdoc integrates with Spring Boot's existing `GlobalExceptionHandler`. If `SWAGGER_ENABLED` is missing or `false`, Spring Boot returns 404 for all Swagger paths — no special handling needed.

---

## Out of scope

- Per-endpoint `@Operation` / `@ApiResponse` annotations — can be added incrementally later.
- Role-based access to the Swagger UI itself (e.g., IP allowlist, HTTP Basic Auth layer) — not needed for a single-user private app.
- Swagger UI in a separate Docker container or standalone deployment.

---

## Files to create / modify

| File | Action |
|---|---|
| `app/pom.xml` | Add `springdoc-openapi-starter-webmvc-ui` dependency |
| `app/src/main/java/.../infrastructure/config/OpenApiConfig.java` | Create |
| `app/src/main/java/.../infrastructure/security/SecurityConfig.java` | Update `permitAll()` |
| `app/src/main/resources/application.properties` | Add two `springdoc.*` properties |
