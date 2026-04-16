package br.com.nathanfiorito.finances.infrastructure.card.mapper;

import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;
import br.com.nathanfiorito.finances.infrastructure.card.entity.InvoicePredictionEntity;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;

public class InvoicePredictionMapper {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private InvoicePredictionMapper() {}

    public static InvoicePrediction toDomain(InvoicePredictionEntity entity) {
        BigDecimal projectedRemaining = BigDecimal.ZERO;
        int basedOnInvoices = 0;
        BigDecimal currentTotal = BigDecimal.ZERO;
        int daysRemaining = 0;
        BigDecimal dailyAverage = BigDecimal.ZERO;
        String confidence = "low";

        if (entity.getPredictionData() != null) {
            try {
                JsonNode node = MAPPER.readTree(entity.getPredictionData());
                if (node.has("projected_remaining")) {
                    projectedRemaining = new BigDecimal(node.get("projected_remaining").asText("0"));
                }
                if (node.has("based_on_invoices")) {
                    basedOnInvoices = node.get("based_on_invoices").asInt(0);
                }
                if (node.has("current_total")) {
                    currentTotal = new BigDecimal(node.get("current_total").asText("0"));
                }
                if (node.has("days_remaining")) {
                    daysRemaining = node.get("days_remaining").asInt(0);
                }
                if (node.has("daily_average")) {
                    dailyAverage = new BigDecimal(node.get("daily_average").asText("0"));
                }
                if (node.has("confidence")) {
                    confidence = node.get("confidence").asText("low");
                }
            } catch (JsonProcessingException e) {
                // Fall through with defaults
            }
        }

        return new InvoicePrediction(
            entity.getCardId(),
            entity.getPredictedTotal(),
            currentTotal,
            daysRemaining,
            dailyAverage,
            entity.getGeneratedAt(),
            confidence,
            projectedRemaining,
            basedOnInvoices
        );
    }
}
