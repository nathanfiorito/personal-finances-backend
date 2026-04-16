package br.com.nathanfiorito.finances.domain.invoice.records;

import java.math.BigDecimal;
import java.time.LocalDate;

public record ExtractedInvoiceItem(
    String tempId,
    LocalDate date,
    String establishment,
    String description,
    BigDecimal amount,
    Integer suggestedCategoryId,
    String suggestedCategoryName,
    String issuerHint,
    boolean isInternational,
    String originalCurrency,
    BigDecimal originalAmount,
    boolean isPossibleDuplicate,
    java.util.UUID duplicateOfTransactionId,
    Double confidence
) {}
