package br.com.nathanfiorito.finances.infrastructure.security;

import br.com.nathanfiorito.finances.infrastructure.telegram.config.TelegramProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class TelegramWebhookFilter extends OncePerRequestFilter {

    private static final String WEBHOOK_PATH = "/webhook";
    private static final String SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token";

    private final TelegramProperties telegramProperties;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !WEBHOOK_PATH.equals(request.getServletPath());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String secret = request.getHeader(SECRET_HEADER);
        if (!telegramProperties.getWebhookSecret().equals(secret)) {
            log.warn("Webhook rejected: invalid secret token from ip={}", request.getRemoteAddr());
            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
            return;
        }
        log.debug("Webhook authenticated: ip={}", request.getRemoteAddr());
        chain.doFilter(request, response);
    }
}
