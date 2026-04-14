package br.com.nathanfiorito.finances.interfaces.rest.swagger;

import br.com.nathanfiorito.finances.interfaces.rest.auth.AuthController;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

// Security returns 403 (not 401) for stateless sessions without auth.
// After Task 5 adds permitAll() for Swagger paths, both return 404 (no handler registered
// in this slice). The tests verify that security is NOT blocking these paths (not 401/403).
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
}
