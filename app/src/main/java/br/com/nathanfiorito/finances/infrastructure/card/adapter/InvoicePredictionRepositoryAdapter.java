package br.com.nathanfiorito.finances.infrastructure.card.adapter;

import br.com.nathanfiorito.finances.domain.card.ports.InvoicePredictionRepository;
import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;
import br.com.nathanfiorito.finances.infrastructure.card.entity.InvoicePredictionEntity;
import br.com.nathanfiorito.finances.infrastructure.card.mapper.InvoicePredictionMapper;
import br.com.nathanfiorito.finances.infrastructure.card.repository.JpaInvoicePredictionRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class InvoicePredictionRepositoryAdapter implements InvoicePredictionRepository {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final JpaInvoicePredictionRepository jpa;

    @Override
    public Optional<InvoicePrediction> findByCardAndMonth(int cardId, LocalDate invoiceMonth) {
        return jpa.findByCardIdAndInvoiceMonth(cardId, invoiceMonth)
            .map(InvoicePredictionMapper::toDomain);
    }

    @Override
    public InvoicePrediction save(int cardId, LocalDate invoiceMonth, InvoicePrediction prediction) {
        InvoicePredictionEntity entity = jpa.findByCardIdAndInvoiceMonth(cardId, invoiceMonth)
            .orElseGet(InvoicePredictionEntity::new);

        entity.setCardId(cardId);
        entity.setInvoiceMonth(invoiceMonth);
        entity.setPredictedTotal(prediction.predictedTotal());
        entity.setGeneratedAt(LocalDateTime.now());
        entity.setPredictionData(buildPredictionData(prediction));

        return InvoicePredictionMapper.toDomain(jpa.save(entity));
    }

    private String buildPredictionData(InvoicePrediction prediction) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("projected_remaining", prediction.projectedRemaining().toPlainString());
        node.put("based_on_invoices", prediction.basedOnInvoices());
        node.put("current_total", prediction.currentTotal().toPlainString());
        node.put("days_remaining", prediction.daysRemaining());
        node.put("daily_average", prediction.dailyAverage().toPlainString());
        node.put("confidence", prediction.confidence());
        return node.toString();
    }
}
