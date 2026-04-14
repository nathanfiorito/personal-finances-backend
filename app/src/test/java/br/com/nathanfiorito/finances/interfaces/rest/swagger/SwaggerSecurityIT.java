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
