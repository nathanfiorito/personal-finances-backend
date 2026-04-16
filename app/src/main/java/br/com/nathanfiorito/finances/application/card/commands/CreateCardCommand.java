package br.com.nathanfiorito.finances.application.card.commands;

public record CreateCardCommand(
    String alias,
    String bank,
    String lastFourDigits,
    int closingDay,
    int dueDay
) {}
