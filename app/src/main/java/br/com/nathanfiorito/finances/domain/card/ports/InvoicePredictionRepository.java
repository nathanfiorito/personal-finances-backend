package br.com.nathanfiorito.finances.domain.card.ports;

import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;
import java.time.LocalDate;
import java.util.Optional;

public interface InvoicePredictionRepository {
    Optional<InvoicePrediction> findByCardAndMonth(int cardId, LocalDate invoiceMonth);
    InvoicePrediction save(int cardId, LocalDate invoiceMonth, InvoicePrediction prediction);
}
