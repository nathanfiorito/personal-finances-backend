package br.com.nathanfiorito.finances.infrastructure.transaction.repository;

import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public interface JpaTransactionRepository extends JpaRepository<TransactionEntity, UUID> {
    List<TransactionEntity> findByDateBetweenAndTransactionType(
        LocalDate start, LocalDate end, TransactionType transactionType);
    List<TransactionEntity> findByDateBetween(LocalDate start, LocalDate end);
    List<TransactionEntity> findAllByOrderByCreatedAtDesc(Pageable pageable);
}
