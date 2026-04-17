package br.com.nathanfiorito.finances.application.invoice.commands;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record ImportInvoiceCommand(
    int cardId,
    List<Item> items
) {
    public record Item(
        LocalDate date,
        String establishment,
        String description,
        BigDecimal amount,
        int categoryId
    ) {}
}
