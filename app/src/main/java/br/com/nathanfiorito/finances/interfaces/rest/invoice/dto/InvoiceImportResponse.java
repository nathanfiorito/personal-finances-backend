package br.com.nathanfiorito.finances.interfaces.rest.invoice.dto;

import java.util.List;
import java.util.UUID;

public record InvoiceImportResponse(
    int importedCount,
    int cardId,
    List<UUID> transactionIds
) {}
