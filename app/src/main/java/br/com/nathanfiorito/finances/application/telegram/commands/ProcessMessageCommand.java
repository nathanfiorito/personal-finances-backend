package br.com.nathanfiorito.finances.application.telegram.commands;

public record ProcessMessageCommand(
    long chatId,
    String entryType,
    String content,
    Long messageId
) {}
