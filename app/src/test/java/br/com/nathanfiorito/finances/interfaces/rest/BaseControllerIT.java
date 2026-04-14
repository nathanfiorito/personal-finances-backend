package br.com.nathanfiorito.finances.interfaces.rest;

import br.com.nathanfiorito.finances.infrastructure.security.JwtAuthFilter;
import br.com.nathanfiorito.finances.infrastructure.security.JwtService;
import br.com.nathanfiorito.finances.infrastructure.security.SecurityConfig;
import br.com.nathanfiorito.finances.infrastructure.security.TelegramWebhookFilter;
import br.com.nathanfiorito.finances.infrastructure.telegram.config.TelegramConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

/**
 * Base class for controller integration tests.
 *
 * Provides a real JwtService (configured with a known test secret) so tests can generate
 * valid Bearer tokens, and imports TelegramConfig so TelegramWebhookFilter gets its
 * required TelegramProperties bean.
 *
 * Imports SecurityConfig explicitly because @WebMvcTest's type filter does not include
 * @EnableWebSecurity configurations via component scan, which means BCryptPasswordEncoder
 * (defined as a @Bean in SecurityConfig) would not be available otherwise.
 *
 * JWT secret decodes to "secret-key-for-integration-tests" (32 bytes — valid for HS256).
 * Admin password hash is BCrypt of "password".
 */
@Import({JwtService.class, TelegramConfig.class, JwtAuthFilter.class, TelegramWebhookFilter.class, SecurityConfig.class})
@TestPropertySource(properties = {
    "jwt.secret=c2VjcmV0LWtleS1mb3ItaW50ZWdyYXRpb24tdGVzdHM=",
    "jwt.expiration-seconds=3600",
    "app.admin.email=admin@test.com",
    "app.admin.password-hash=$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy",
    "app.cors.allowed-origins=http://localhost:3000",
    "telegram.bot-token=test-bot-token",
    "telegram.webhook-secret=test-webhook-secret",
    "telegram.allowed-chat-id=123456",
    "app.api.base-path=/api/v1"
})
public abstract class BaseControllerIT {

    @Autowired
    protected MockMvc mockMvc;

    @Autowired
    private JwtService jwtService;

    protected String validToken() {
        return "Bearer " + jwtService.generate("admin@test.com");
    }
}
