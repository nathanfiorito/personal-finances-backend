package br.com.nathanfiorito.finances.interfaces.rest.auth;

import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AuthController.class)
class AuthControllerIT extends BaseControllerIT {

    @Test
    void loginShouldReturnJwtTokenWhenCredentialsAreValid() throws Exception {
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"email": "admin@test.com", "password": "password"}
                        """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.token").isNotEmpty())
            .andExpect(jsonPath("$.expires_in").isNumber());
    }

    @Test
    void loginShouldReturnUnauthorizedWhenPasswordIsWrong() throws Exception {
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"email": "admin@test.com", "password": "wrongpassword"}
                        """))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void loginShouldReturnUnauthorizedWhenEmailIsWrong() throws Exception {
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"email": "other@test.com", "password": "password"}
                        """))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void loginShouldReturnBadRequestWhenBodyIsMissing() throws Exception {
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest());
    }
}
