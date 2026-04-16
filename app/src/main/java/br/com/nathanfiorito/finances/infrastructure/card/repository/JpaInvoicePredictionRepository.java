package br.com.nathanfiorito.finances.infrastructure.card.repository;

import br.com.nathanfiorito.finances.infrastructure.card.entity.InvoicePredictionEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.Optional;

public interface JpaInvoicePredictionRepository extends JpaRepository<InvoicePredictionEntity, Integer> {
    Optional<InvoicePredictionEntity> findByCardIdAndInvoiceMonth(int cardId, LocalDate invoiceMonth);
}
