package br.com.nathanfiorito.finances.interfaces.telegram.dto;

import java.util.List;

/**
 * Minimal Telegram Update DTO — only the fields used by this application.
 * Jackson's global SNAKE_CASE strategy maps camelCase fields to snake_case JSON keys automatically.
 */
public record TelegramUpdateDto(
    long updateId,
    MessageDto message,
    CallbackQueryDto callbackQuery
) {
    public record MessageDto(
        int messageId,
        ChatDto chat,
        String text,
        List<PhotoSizeDto> photo,
        DocumentDto document
    ) {}

    public record ChatDto(long id) {}

    public record PhotoSizeDto(
        String fileId,
        int width,
        int height
    ) {}

    public record DocumentDto(
        String fileId,
        String fileName,
        String mimeType
    ) {}

    public record CallbackQueryDto(
        String id,
        MessageDto message,
        String data
    ) {}
}
