package br.com.nathanfiorito.finances.infrastructure.transaction.adapter;

import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;
import br.com.nathanfiorito.finances.infrastructure.card.entity.CardEntity;
import br.com.nathanfiorito.finances.infrastructure.card.repository.JpaCardRepository;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.category.repository.JpaCategoryRepository;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;
import br.com.nathanfiorito.finances.infrastructure.transaction.mapper.TransactionMapper;
import br.com.nathanfiorito.finances.infrastructure.transaction.repository.JpaTransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TransactionRepositoryAdapter implements TransactionRepository {

    private final JpaTransactionRepository jpa;
    private final JpaCategoryRepository categoryJpa;
    private final JpaCardRepository cardJpa;

    @Override
    @Transactional
    public Transaction save(ExtractedTransaction extracted, int categoryId) {
        return save(extracted, categoryId, null);
    }

    @Override
    @Transactional
    public Transaction save(ExtractedTransaction extracted, int categoryId, Integer cardId) {
        CategoryEntity category = categoryJpa.findById(categoryId)
            .orElseThrow(() -> new CategoryNotFoundException(categoryId));
        TransactionEntity entity = TransactionMapper.toEntity(extracted, category);
        if (cardId != null) {
            CardEntity card = cardJpa.findById(cardId)
                .orElseThrow(() -> new CardNotFoundException(cardId));
            entity.setCard(card);
        }
        return TransactionMapper.toDomain(jpa.save(entity));
    }

    @Override
    public List<Transaction> listByCardAndPeriod(int cardId, LocalDate start, LocalDate end) {
        return jpa.findByCardIdAndDateBetween(cardId, start, end)
            .stream().map(TransactionMapper::toDomain).toList();
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
    public List<Transaction> listByPeriod(LocalDate start, LocalDate end, Optional<TransactionType> type) {
        List<TransactionEntity> entities = type.isPresent()
            ? jpa.findByDateBetweenAndTransactionType(start, end, type.get())
            : jpa.findByDateBetween(start, end);
        return entities.stream().map(TransactionMapper::toDomain).toList();
    }

    @Override
    public List<Transaction> listRecent(int limit) {
        return jpa.findAllByOrderByCreatedAtDesc(PageRequest.of(0, limit))
            .stream().map(TransactionMapper::toDomain).toList();
    }

    @Override
    @Transactional
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
            if (data.cardId() != null) {
                CardEntity card = cardJpa.findById(data.cardId())
                    .orElseThrow(() -> new CardNotFoundException(data.cardId()));
                entity.setCard(card);
            } else if (data.paymentMethod() != null &&
                       data.paymentMethod() != br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod.CREDIT) {
                entity.setCard(null);
            }
            return TransactionMapper.toDomain(jpa.save(entity));
        });
    }

    @Override
    @Transactional
    public boolean delete(UUID id) {
        if (!jpa.existsById(id)) return false;
        jpa.deleteById(id);
        return true;
    }
}
