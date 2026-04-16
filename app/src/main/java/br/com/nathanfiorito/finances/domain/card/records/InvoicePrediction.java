package br.com.nathanfiorito.finances.domain.card.records;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record InvoicePrediction(
    int cardId,
    BigDecimal predictedTotal,
    BigDecimal currentTotal,
    int daysRemaining,
    BigDecimal dailyAverage,
    LocalDateTime generatedAt,
    String confidence,
    BigDecimal projectedRemaining,
    int basedOnInvoices
) {}
