package br.com.nathanfiorito.finances.interfaces.rest.auth;

import br.com.nathanfiorito.finances.infrastructure.security.JwtService;
import br.com.nathanfiorito.finances.interfaces.rest.auth.dto.LoginRequest;
import br.com.nathanfiorito.finances.interfaces.rest.auth.dto.LoginResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirements;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    @Value("${app.admin.email}")
    private String adminEmail;

    @Value("${app.admin.password-hash}")
    private String adminPasswordHash;

    private final BCryptPasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    @SecurityRequirements
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody @Valid LoginRequest request) {
        if (!request.email().equalsIgnoreCase(adminEmail) ||
            !passwordEncoder.matches(request.password(), adminPasswordHash)) {
            log.warn("Login failed: email={}", request.email());
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
        String token = jwtService.generate(adminEmail);
        log.info("Login successful: email={}", request.email());
        return ResponseEntity.ok(new LoginResponse(token, jwtService.getExpirationSeconds()));
    }
}
