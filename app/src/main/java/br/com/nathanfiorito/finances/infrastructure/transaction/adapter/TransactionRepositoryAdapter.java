package br.com.nathanfiorito.finances.infrastructure.transaction.adapter;

import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.category.repository.JpaCategoryRepository;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;
import br.com.nathanfiorito.finances.infrastructure.transaction.mapper.TransactionMapper;
import br.com.nathanfiorito.finances.infrastructure.transaction.repository.JpaTransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class TransactionRepositoryAdapter implements TransactionRepository {

    private final JpaTransactionRepository jpa;
    private final JpaCategoryRepository categoryJpa;

    @Override
    public Transaction save(ExtractedTransaction extracted, int categoryId) {
        CategoryEntity category = categoryJpa.findById(categoryId)
            .orElseThrow(() -> new CategoryNotFoundException(categoryId));
        TransactionEntity entity = TransactionMapper.toEntity(extracted, category);
        return TransactionMapper.toDomain(jpa.save(entity));
    }

    @Override
    public Optional<Transaction> findById(UUID id) {
        return jpa.findById(id).map(TransactionMapper::toDomain);
    }

    @Override
    public PageResult<Transaction> listPaginated(int page, int pageSize) {
        Page<TransactionEntity> result = jpa.findAll(PageRequest.of(page, pageSize));
        return new PageResult<>(
            result.getContent().stream().map(TransactionMapper::toDomain).toList(),
            (int) result.getTotalElements()
        );
    }

    @Override
    public List<Transaction> listByPeriod(LocalDate start, LocalDate end, TransactionType type) {
        return jpa.findByDateBetweenAndTransactionType(start, end, type)
            .stream().map(TransactionMapper::toDomain).toList();
    }

    @Override
    public Optional<Transaction> update(UUID id, TransactionUpdate data) {
        return jpa.findById(id).map(entity -> {
            if (data.amount() != null)          entity.setAmount(data.amount());
            if (data.date() != null)            entity.setDate(data.date());
            if (data.establishment() != null)   entity.setEstablishment(data.establishment());
            if (data.description() != null)     entity.setDescription(data.description());
            if (data.paymentMethod() != null)   entity.setPaymentMethod(data.paymentMethod());
            if (data.transactionType() != null) entity.setTransactionType(data.transactionType());
            if (data.categoryId() != null) {
                CategoryEntity cat = categoryJpa.findById(data.categoryId())
                    .orElseThrow(() -> new CategoryNotFoundException(data.categoryId()));
                entity.setCategory(cat);
            }
            return TransactionMapper.toDomain(jpa.save(entity));
        });
    }

    @Override
    public boolean delete(UUID id) {
        if (!jpa.existsById(id)) return false;
        jpa.deleteById(id);
        return true;
    }
}
