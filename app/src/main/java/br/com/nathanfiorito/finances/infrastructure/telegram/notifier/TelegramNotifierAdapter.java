package br.com.nathanfiorito.finances.infrastructure.telegram.notifier;

import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.infrastructure.telegram.config.TelegramProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
public class TelegramNotifierAdapter implements NotifierPort {

    private final RestClient client;

    public TelegramNotifierAdapter(RestClient.Builder builder, TelegramProperties properties) {
        this.client = builder
            .baseUrl("https://api.telegram.org/bot" + properties.getBotToken())
            .build();
    }

    @Override
    public void sendMessage(long chatId, String text, String parseMode, List<List<NotificationButton>> buttons) {
        Map<String, Object> body = new HashMap<>();
        body.put("chat_id", chatId);
        body.put("text", text);
        if (parseMode != null) body.put("parse_mode", parseMode);
        if (buttons != null && !buttons.isEmpty()) body.put("reply_markup", buildInlineKeyboard(buttons));
        post("/sendMessage", body);
    }

    @Override
    public void editMessage(long chatId, long messageId, String text, String parseMode,
                            List<List<NotificationButton>> buttons) {
        Map<String, Object> body = new HashMap<>();
        body.put("chat_id", chatId);
        body.put("message_id", messageId);
        body.put("text", text);
        if (parseMode != null) body.put("parse_mode", parseMode);
        if (buttons != null) {
            body.put("reply_markup", buttons.isEmpty()
                ? Map.of("inline_keyboard", List.of())
                : buildInlineKeyboard(buttons));
        }
        post("/editMessageText", body);
    }

    @Override
    public void answerCallback(String callbackId, String text) {
        Map<String, Object> body = new HashMap<>();
        body.put("callback_query_id", callbackId);
        if (text != null) body.put("text", text);
        post("/answerCallbackQuery", body);
    }

    @Override
    public void sendFile(long chatId, byte[] content, String filename, String caption) {
        MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
        parts.add("chat_id", chatId);
        parts.add("caption", caption);
        parts.add("document", new ByteArrayResource(content) {
            @Override
            public String getFilename() {
                return filename;
            }
        });
        client.post()
            .uri("/sendDocument")
            .contentType(MediaType.MULTIPART_FORM_DATA)
            .body(parts)
            .retrieve()
            .toBodilessEntity();
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private void post(String endpoint, Map<String, Object> body) {
        try {
            client.post()
                .uri(endpoint)
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .toBodilessEntity();
        } catch (Exception e) {
            log.warn("Telegram API call to {} failed: {}", endpoint, e.getMessage());
        }
    }

    private Map<String, Object> buildInlineKeyboard(List<List<NotificationButton>> buttons) {
        List<List<Map<String, String>>> keyboard = buttons.stream()
            .map(row -> row.stream()
                .map(btn -> Map.of("text", btn.text(), "callback_data", btn.callbackData()))
                .toList())
            .toList();
        return Map.of("inline_keyboard", keyboard);
    }
}
