package br.com.nathanfiorito.finances.interfaces.rest.invoice.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record InvoiceImportPreviewResponse(
    String sourceFileName,
    DetectedCardDto detectedCard,
    List<Item> items
) {
    public record DetectedCardDto(
        String lastFourDigits,
        Integer matchedCardId,
        String matchedCardAlias,
        String matchedCardBank
    ) {}

    public record Item(
        String tempId,
        LocalDate date,
        String establishment,
        String description,
        BigDecimal amount,
        String transactionType,
        String paymentMethod,
        Integer suggestedCategoryId,
        String suggestedCategoryName,
        String issuerHint,
        boolean isInternational,
        String originalCurrency,
        BigDecimal originalAmount,
        boolean isPossibleDuplicate,
        UUID duplicateOfTransactionId,
        Double confidence
    ) {}
}
