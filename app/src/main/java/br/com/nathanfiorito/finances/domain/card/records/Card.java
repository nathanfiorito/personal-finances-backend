package br.com.nathanfiorito.finances.domain.card.records;

import java.time.LocalDateTime;

public record Card(
    int id,
    String alias,
    String bank,
    String lastFourDigits,
    int closingDay,
    int dueDay,
    boolean active,
    LocalDateTime createdAt
) {}
