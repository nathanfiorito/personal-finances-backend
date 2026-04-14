package br.com.nathanfiorito.finances.infrastructure.telegram.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "telegram")
public class TelegramProperties {
    private String botToken;
    private String webhookSecret;
    private long allowedChatId;
}
