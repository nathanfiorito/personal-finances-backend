package br.com.nathanfiorito.finances.application.telegram.commands;

public record ConfirmTransactionCommand(
    long chatId,
    long messageId,
    boolean skipDuplicateCheck
) {}
