package br.com.nathanfiorito.finances.application.card.commands;

public record UpdateCardCommand(
    int id,
    String alias,
    String bank,
    String lastFourDigits,
    int closingDay,
    int dueDay
) {}
