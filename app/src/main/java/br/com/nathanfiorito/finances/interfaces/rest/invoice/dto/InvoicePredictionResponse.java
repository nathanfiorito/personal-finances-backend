package br.com.nathanfiorito.finances.interfaces.rest.invoice.dto;

import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;

public record InvoicePredictionResponse(
    int cardId,
    String predictedTotal,
    String currentTotal,
    int daysRemaining,
    String dailyAverage,
    String generatedAt,
    String confidence,
    String projectedRemaining,
    int basedOnInvoices
) {
    public static InvoicePredictionResponse from(InvoicePrediction prediction) {
        return new InvoicePredictionResponse(
            prediction.cardId(),
            prediction.predictedTotal().toPlainString(),
            prediction.currentTotal().toPlainString(),
            prediction.daysRemaining(),
            prediction.dailyAverage().toPlainString(),
            prediction.generatedAt() != null ? prediction.generatedAt().toString() : null,
            prediction.confidence(),
            prediction.projectedRemaining().toPlainString(),
            prediction.basedOnInvoices()
        );
    }
}
