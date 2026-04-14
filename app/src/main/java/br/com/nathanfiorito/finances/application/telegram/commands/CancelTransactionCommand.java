package br.com.nathanfiorito.finances.application.telegram.commands;

public record CancelTransactionCommand(long chatId, long messageId) {}
