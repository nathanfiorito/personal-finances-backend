package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.card.ports.InvoicePredictionRepository;
import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public class StubInvoicePredictionRepository implements InvoicePredictionRepository {

    private final Map<String, InvoicePrediction> store = new HashMap<>();

    @Override
    public Optional<InvoicePrediction> findByCardAndMonth(int cardId, LocalDate invoiceMonth) {
        return Optional.ofNullable(store.get(key(cardId, invoiceMonth)));
    }

    @Override
    public InvoicePrediction save(int cardId, LocalDate invoiceMonth, InvoicePrediction prediction) {
        store.put(key(cardId, invoiceMonth), prediction);
        return prediction;
    }

    private String key(int cardId, LocalDate month) {
        return cardId + ":" + month;
    }
}
