package br.com.nathanfiorito.finances.infrastructure.transaction.repository;

import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface JpaTransactionRepository extends JpaRepository<TransactionEntity, UUID> {

    @Override
    @EntityGraph(attributePaths = {"category"})
    Page<TransactionEntity> findAll(Pageable pageable);

    @Override
    @EntityGraph(attributePaths = {"category"})
    Optional<TransactionEntity> findById(UUID id);

    @EntityGraph(attributePaths = {"category"})
    List<TransactionEntity> findByDateBetweenAndTransactionType(
        LocalDate start, LocalDate end, TransactionType transactionType);

    @EntityGraph(attributePaths = {"category"})
    List<TransactionEntity> findByDateBetween(LocalDate start, LocalDate end);

    @EntityGraph(attributePaths = {"category"})
    List<TransactionEntity> findAllByOrderByCreatedAtDesc(Pageable pageable);
}
