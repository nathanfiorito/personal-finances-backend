package br.com.nathanfiorito.finances.interfaces.rest.swagger;

import br.com.nathanfiorito.finances.interfaces.rest.auth.AuthController;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

// Verifies that Spring Security does not block Swagger paths (not 401/403).
// When permitted, requests return 404 (no springdoc handler registered in this slice).
// AuthController.class is chosen arbitrarily — any controller works here since the
// tests only exercise the security filter chain, not the MVC dispatcher.
@WebMvcTest(AuthController.class)
class SwaggerSecurityIT extends BaseControllerIT {

    @Test
    void apiDocsShouldNotBeBlockedBySecurity() throws Exception {
        var result = mockMvc.perform(get("/v3/api-docs")).andReturn();
        assertThat(result.getResponse().getStatus()).isNotIn(List.of(401, 403));
    }

    @Test
    void swaggerUiShouldNotBeBlockedBySecurity() throws Exception {
        var result = mockMvc.perform(get("/swagger-ui/index.html")).andReturn();
        assertThat(result.getResponse().getStatus()).isNotIn(List.of(401, 403));
    }

    @Test
    void swaggerUiHtmlShouldNotBeBlockedBySecurity() throws Exception {
        var result = mockMvc.perform(get("/swagger-ui.html")).andReturn();
        assertThat(result.getResponse().getStatus()).isNotIn(List.of(401, 403));
    }
}
