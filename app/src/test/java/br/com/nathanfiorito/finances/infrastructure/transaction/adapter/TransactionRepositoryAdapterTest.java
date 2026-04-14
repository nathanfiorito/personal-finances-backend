package br.com.nathanfiorito.finances.infrastructure.transaction.adapter;

import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.category.repository.JpaCategoryRepository;
import br.com.nathanfiorito.finances.infrastructure.transaction.entity.TransactionEntity;
import br.com.nathanfiorito.finances.infrastructure.transaction.repository.JpaTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class TransactionRepositoryAdapterTest {

    private StubJpaTransactionRepository transactionJpa;
    private StubJpaCategoryRepository categoryJpa;
    private TransactionRepositoryAdapter adapter;

    @BeforeEach
    void setUp() {
        transactionJpa = new StubJpaTransactionRepository();
        categoryJpa = new StubJpaCategoryRepository();
        adapter = new TransactionRepositoryAdapter(transactionJpa, categoryJpa);
    }

    // --- Helper factories ---

    private CategoryEntity buildCategory(int id, String name) {
        CategoryEntity cat = new CategoryEntity();
        cat.setId(id);
        cat.setName(name);
        cat.setActive(true);
        return cat;
    }

    private TransactionEntity buildEntity(UUID id, BigDecimal amount, CategoryEntity category) {
        TransactionEntity entity = new TransactionEntity();
        entity.setId(id);
        entity.setAmount(amount);
        entity.setDate(LocalDate.of(2024, 1, 15));
        entity.setEstablishment("Supermercado");
        entity.setDescription("Weekly groceries");
        entity.setCategory(category);
        entity.setTaxId(null);
        entity.setEntryType("text");
        entity.setTransactionType(TransactionType.EXPENSE);
        entity.setPaymentMethod(PaymentMethod.CREDIT);
        entity.setConfidence(0.95);
        entity.setCreatedAt(LocalDateTime.now());
        entity.setUpdatedAt(LocalDateTime.now());
        return entity;
    }

    private ExtractedTransaction buildExtracted() {
        return new ExtractedTransaction(
            new BigDecimal("50.00"),
            LocalDate.of(2024, 1, 15),
            "Supermercado",
            "Weekly groceries",
            null,
            "text",
            TransactionType.EXPENSE,
            PaymentMethod.CREDIT,
            0.95
        );
    }

    // --- Tests ---

    @Test
    void saveShouldPersistAndReturnTransactionWhenCategoryFound() {
        CategoryEntity category = buildCategory(1, "Food");
        categoryJpa.store(1, category);

        Transaction result = adapter.save(buildExtracted(), 1);

        assertThat(result).isNotNull();
        assertThat(result.amount()).isEqualByComparingTo(new BigDecimal("50.00"));
        assertThat(result.establishment()).isEqualTo("Supermercado");
        assertThat(result.categoryId()).isEqualTo(1);
        assertThat(transactionJpa.lastSavedEntity).isNotNull();
    }

    @Test
    void saveShouldThrowCategoryNotFoundExceptionWhenCategoryMissing() {
        assertThatThrownBy(() -> adapter.save(buildExtracted(), 99))
            .isInstanceOf(CategoryNotFoundException.class)
            .hasMessageContaining("99");
    }

    @Test
    void findByIdShouldReturnTransactionWhenFound() {
        UUID id = UUID.randomUUID();
        CategoryEntity category = buildCategory(1, "Food");
        TransactionEntity entity = buildEntity(id, new BigDecimal("50.00"), category);
        transactionJpa.store(id, entity);

        Optional<Transaction> result = adapter.findById(id);

        assertThat(result).isPresent();
        assertThat(result.get().id()).isEqualTo(id);
        assertThat(result.get().amount()).isEqualByComparingTo(new BigDecimal("50.00"));
    }

    @Test
    void findByIdShouldReturnEmptyWhenNotFound() {
        Optional<Transaction> result = adapter.findById(UUID.randomUUID());
        assertThat(result).isEmpty();
    }

    @Test
    void listPaginatedShouldReturnPageResultWithCorrectItemsAndTotal() {
        CategoryEntity category = buildCategory(1, "Food");
        UUID id1 = UUID.randomUUID();
        UUID id2 = UUID.randomUUID();
        transactionJpa.store(id1, buildEntity(id1, new BigDecimal("10.00"), category));
        transactionJpa.store(id2, buildEntity(id2, new BigDecimal("20.00"), category));

        PageResult<Transaction> result = adapter.listPaginated(0, 10);

        assertThat(result.items()).hasSize(2);
        assertThat(result.total()).isEqualTo(2);
    }

    @Test
    void listByPeriodShouldReturnFilteredTransactions() {
        CategoryEntity category = buildCategory(1, "Food");
        UUID id1 = UUID.randomUUID();
        UUID id2 = UUID.randomUUID();

        TransactionEntity entity1 = buildEntity(id1, new BigDecimal("30.00"), category);
        entity1.setDate(LocalDate.of(2024, 1, 10));
        entity1.setTransactionType(TransactionType.EXPENSE);

        TransactionEntity entity2 = buildEntity(id2, new BigDecimal("40.00"), category);
        entity2.setDate(LocalDate.of(2024, 1, 20));
        entity2.setTransactionType(TransactionType.EXPENSE);

        transactionJpa.store(id1, entity1);
        transactionJpa.store(id2, entity2);

        List<Transaction> result = adapter.listByPeriod(
            LocalDate.of(2024, 1, 1),
            LocalDate.of(2024, 1, 31),
            TransactionType.EXPENSE
        );

        assertThat(result).hasSize(2);
        assertThat(result).extracting(Transaction::transactionType)
            .containsOnly(TransactionType.EXPENSE);
    }

    @Test
    void updateShouldChangeFieldsAndReturnUpdatedTransaction() {
        UUID id = UUID.randomUUID();
        CategoryEntity category = buildCategory(1, "Food");
        TransactionEntity entity = buildEntity(id, new BigDecimal("50.00"), category);
        transactionJpa.store(id, entity);

        TransactionUpdate update = new TransactionUpdate(
            new BigDecimal("99.99"),
            null,
            "NewEstablishment",
            null,
            null,
            null,
            null
        );

        Optional<Transaction> result = adapter.update(id, update);

        assertThat(result).isPresent();
        assertThat(result.get().amount()).isEqualByComparingTo(new BigDecimal("99.99"));
        assertThat(result.get().establishment()).isEqualTo("NewEstablishment");
    }

    @Test
    void updateShouldThrowCategoryNotFoundExceptionWhenCategoryIdIsInvalid() {
        UUID id = UUID.randomUUID();
        CategoryEntity category = buildCategory(1, "Food");
        transactionJpa.store(id, buildEntity(id, new BigDecimal("50.00"), category));

        TransactionUpdate update = new TransactionUpdate(
            null, null, null, null,
            99, // non-existent categoryId
            null, null
        );

        assertThatThrownBy(() -> adapter.update(id, update))
            .isInstanceOf(CategoryNotFoundException.class)
            .hasMessageContaining("99");
    }

    @Test
    void updateShouldReturnEmptyWhenTransactionNotFound() {
        TransactionUpdate update = new TransactionUpdate(
            new BigDecimal("99.99"), null, null, null, null, null, null
        );

        Optional<Transaction> result = adapter.update(UUID.randomUUID(), update);
        assertThat(result).isEmpty();
    }

    @Test
    void deleteShouldReturnTrueWhenTransactionExists() {
        UUID id = UUID.randomUUID();
        CategoryEntity category = buildCategory(1, "Food");
        transactionJpa.store(id, buildEntity(id, new BigDecimal("50.00"), category));

        boolean result = adapter.delete(id);

        assertThat(result).isTrue();
        assertThat(transactionJpa.existsById(id)).isFalse();
    }

    @Test
    void deleteShouldReturnFalseWhenTransactionNotFound() {
        boolean result = adapter.delete(UUID.randomUUID());
        assertThat(result).isFalse();
    }

    // --- Stubs ---

    static class StubJpaTransactionRepository implements JpaTransactionRepository {
        private final Map<UUID, TransactionEntity> store = new HashMap<>();
        TransactionEntity lastSavedEntity;

        void store(UUID id, TransactionEntity entity) {
            store.put(id, entity);
        }

        @Override
        public TransactionEntity save(TransactionEntity entity) {
            if (entity.getId() == null) {
                entity.setId(UUID.randomUUID());
                entity.setCreatedAt(LocalDateTime.now());
                entity.setUpdatedAt(LocalDateTime.now());
            }
            lastSavedEntity = entity;
            store.put(entity.getId(), entity);
            return entity;
        }

        @Override
        public Optional<TransactionEntity> findById(UUID id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public boolean existsById(UUID id) {
            return store.containsKey(id);
        }

        @Override
        public void deleteById(UUID id) {
            store.remove(id);
        }

        @Override
        public Page<TransactionEntity> findAll(Pageable pageable) {
            List<TransactionEntity> all = store.values().stream().toList();
            return new PageImpl<>(all, pageable, all.size());
        }

        @Override
        public List<TransactionEntity> findByDateBetweenAndTransactionType(
                LocalDate start, LocalDate end, TransactionType type) {
            return store.values().stream()
                .filter(e -> !e.getDate().isBefore(start) && !e.getDate().isAfter(end))
                .filter(e -> e.getTransactionType() == type)
                .toList();
        }

        @Override
        public void flush() {}

        @Override
        public <S extends TransactionEntity> S saveAndFlush(S entity) {
            return (S) save(entity);
        }

        @Override
        public <S extends TransactionEntity> List<S> saveAllAndFlush(Iterable<S> entities) {
            return null;
        }

        @Override
        public void deleteInBatch(Iterable<TransactionEntity> entities) {}

        @Override
        public void deleteAllInBatch() {}

        @Override
        public void deleteAllInBatch(Iterable<TransactionEntity> entities) {}

        @Override
        public void deleteAllByIdInBatch(Iterable<UUID> ids) {}

        @Override
        public void deleteAll() {}

        @Override
        public void deleteAll(Iterable<? extends TransactionEntity> entities) {}

        @Override
        public TransactionEntity getOne(UUID id) {
            return store.get(id);
        }

        @Override
        public TransactionEntity getById(UUID id) {
            return store.get(id);
        }

        @Override
        public TransactionEntity getReferenceById(UUID id) {
            return store.get(id);
        }

        @Override
        public <S extends TransactionEntity> List<S> saveAll(Iterable<S> entities) {
            return null;
        }

        @Override
        public List<TransactionEntity> findAll() {
            return store.values().stream().toList();
        }

        @Override
        public List<TransactionEntity> findAllById(Iterable<UUID> ids) {
            return null;
        }

        @Override
        public long count() {
            return store.size();
        }

        @Override
        public void deleteAllById(Iterable<? extends UUID> ids) {}

        @Override
        public void delete(TransactionEntity entity) {
            if (entity != null && entity.getId() != null) {
                store.remove(entity.getId());
            }
        }

        @Override
        public <S extends TransactionEntity> boolean exists(org.springframework.data.domain.Example<S> example) {
            return false;
        }

        @Override
        public <S extends TransactionEntity> long count(org.springframework.data.domain.Example<S> example) {
            return 0;
        }

        @Override
        public <S extends TransactionEntity> List<S> findAll(org.springframework.data.domain.Example<S> example) {
            return null;
        }

        @Override
        public <S extends TransactionEntity> List<S> findAll(org.springframework.data.domain.Example<S> example, org.springframework.data.domain.Sort sort) {
            return null;
        }

        @Override
        public <S extends TransactionEntity> Page<S> findAll(org.springframework.data.domain.Example<S> example, Pageable pageable) {
            return null;
        }

        @Override
        public <S extends TransactionEntity> Optional<S> findOne(org.springframework.data.domain.Example<S> example) {
            return Optional.empty();
        }

        @Override
        public List<TransactionEntity> findAll(org.springframework.data.domain.Sort sort) {
            return store.values().stream().toList();
        }

        @Override
        public <S extends TransactionEntity, R> R findBy(org.springframework.data.domain.Example<S> example, java.util.function.Function<org.springframework.data.repository.query.FluentQuery.FetchableFluentQuery<S>, R> queryFunction) {
            return null;
        }
    }

    static class StubJpaCategoryRepository implements JpaCategoryRepository {
        private final Map<Integer, CategoryEntity> store = new HashMap<>();

        void store(Integer id, CategoryEntity entity) {
            store.put(id, entity);
        }

        @Override
        public CategoryEntity save(CategoryEntity entity) {
            store.put(entity.getId(), entity);
            return entity;
        }

        @Override
        public Optional<CategoryEntity> findById(Integer id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public boolean existsById(Integer id) {
            return store.containsKey(id);
        }

        @Override
        public void deleteById(Integer id) {
            store.remove(id);
        }

        @Override
        public Page<CategoryEntity> findByActiveTrue(Pageable pageable) {
            List<CategoryEntity> active = store.values().stream()
                .filter(CategoryEntity::isActive)
                .toList();
            return new PageImpl<>(active, pageable, active.size());
        }

        @Override
        public Page<CategoryEntity> findAll(Pageable pageable) {
            List<CategoryEntity> all = store.values().stream().toList();
            return new PageImpl<>(all, pageable, all.size());
        }

        @Override
        public void flush() {}

        @Override
        public <S extends CategoryEntity> S saveAndFlush(S entity) {
            return (S) save(entity);
        }

        @Override
        public <S extends CategoryEntity> List<S> saveAllAndFlush(Iterable<S> entities) {
            return null;
        }

        @Override
        public void deleteInBatch(Iterable<CategoryEntity> entities) {}

        @Override
        public void deleteAllInBatch() {}

        @Override
        public void deleteAllInBatch(Iterable<CategoryEntity> entities) {}

        @Override
        public void deleteAllByIdInBatch(Iterable<Integer> ids) {}

        @Override
        public void deleteAll() {}

        @Override
        public void deleteAll(Iterable<? extends CategoryEntity> entities) {}

        @Override
        public CategoryEntity getOne(Integer id) {
            return store.get(id);
        }

        @Override
        public CategoryEntity getById(Integer id) {
            return store.get(id);
        }

        @Override
        public CategoryEntity getReferenceById(Integer id) {
            return store.get(id);
        }

        @Override
        public <S extends CategoryEntity> List<S> saveAll(Iterable<S> entities) {
            return null;
        }

        @Override
        public List<CategoryEntity> findAll() {
            return store.values().stream().toList();
        }

        @Override
        public List<CategoryEntity> findAllById(Iterable<Integer> ids) {
            return null;
        }

        @Override
        public long count() {
            return store.size();
        }

        @Override
        public void deleteAllById(Iterable<? extends Integer> ids) {}

        @Override
        public void delete(CategoryEntity entity) {
            if (entity != null && entity.getId() != null) {
                store.remove(entity.getId());
            }
        }

        @Override
        public <S extends CategoryEntity> boolean exists(org.springframework.data.domain.Example<S> example) {
            return false;
        }

        @Override
        public <S extends CategoryEntity> long count(org.springframework.data.domain.Example<S> example) {
            return 0;
        }

        @Override
        public <S extends CategoryEntity> List<S> findAll(org.springframework.data.domain.Example<S> example) {
            return null;
        }

        @Override
        public <S extends CategoryEntity> List<S> findAll(org.springframework.data.domain.Example<S> example, org.springframework.data.domain.Sort sort) {
            return null;
        }

        @Override
        public <S extends CategoryEntity> Page<S> findAll(org.springframework.data.domain.Example<S> example, Pageable pageable) {
            return null;
        }

        @Override
        public <S extends CategoryEntity> Optional<S> findOne(org.springframework.data.domain.Example<S> example) {
            return Optional.empty();
        }

        @Override
        public List<CategoryEntity> findAll(org.springframework.data.domain.Sort sort) {
            return store.values().stream().toList();
        }

        @Override
        public <S extends CategoryEntity, R> R findBy(org.springframework.data.domain.Example<S> example, java.util.function.Function<org.springframework.data.repository.query.FluentQuery.FetchableFluentQuery<S>, R> queryFunction) {
            return null;
        }
    }
}
