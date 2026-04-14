package br.com.nathanfiorito.finances.infrastructure.transaction.adapter;

import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;
import br.com.nathanfiorito.finances.infrastructure.BaseRepositoryIT;
import br.com.nathanfiorito.finances.infrastructure.category.adapter.CategoryRepositoryAdapter;
import br.com.nathanfiorito.finances.infrastructure.category.repository.JpaCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Import;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@Import({TransactionRepositoryAdapter.class, CategoryRepositoryAdapter.class})
class TransactionRepositoryAdapterIT extends BaseRepositoryIT {

    @Autowired
    private TransactionRepositoryAdapter adapter;

    @Autowired
    private JpaCategoryRepository categoryJpa;

    private int categoryId;

    @BeforeEach
    void setUp() {
        var cat = new br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity();
        cat.setName("Food");
        cat.setActive(true);
        categoryId = categoryJpa.save(cat).getId();
    }

    private ExtractedTransaction buildExtracted(BigDecimal amount, LocalDate date, TransactionType type) {
        return new ExtractedTransaction(
            amount,
            date,
            "Supermercado",
            "Test purchase",
            null,
            "text",
            type,
            PaymentMethod.CREDIT,
            0.95
        );
    }

    private ExtractedTransaction defaultExtracted() {
        return buildExtracted(new BigDecimal("50.00"), LocalDate.of(2024, 6, 15), TransactionType.EXPENSE);
    }

    @Test
    void saveShouldPersistTransactionAndGenerateUuid() {
        Transaction result = adapter.save(defaultExtracted(), categoryId);

        assertThat(result.id()).isNotNull();
        assertThat(result.amount()).isEqualByComparingTo(new BigDecimal("50.00"));
        assertThat(result.establishment()).isEqualTo("Supermercado");
        assertThat(result.categoryId()).isEqualTo(categoryId);
        assertThat(result.category()).isEqualTo("Food");
        assertThat(result.transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(result.createdAt()).isNotNull();
    }

    @Test
    void saveShouldThrowCategoryNotFoundExceptionWhenCategoryDoesNotExist() {
        assertThatThrownBy(() -> adapter.save(defaultExtracted(), Integer.MAX_VALUE))
            .isInstanceOf(CategoryNotFoundException.class);
    }

    @Test
    void findByIdShouldReturnTransactionWhenFound() {
        Transaction saved = adapter.save(defaultExtracted(), categoryId);

        Optional<Transaction> result = adapter.findById(saved.id());

        assertThat(result).isPresent();
        assertThat(result.get().id()).isEqualTo(saved.id());
        assertThat(result.get().amount()).isEqualByComparingTo(new BigDecimal("50.00"));
    }

    @Test
    void findByIdShouldReturnEmptyWhenNotFound() {
        Optional<Transaction> result = adapter.findById(UUID.randomUUID());

        assertThat(result).isEmpty();
    }

    @Test
    void listPaginatedShouldReturnCorrectItemsAndTotal() {
        adapter.save(buildExtracted(new BigDecimal("10.00"), LocalDate.of(2024, 1, 1), TransactionType.EXPENSE), categoryId);
        adapter.save(buildExtracted(new BigDecimal("20.00"), LocalDate.of(2024, 1, 2), TransactionType.EXPENSE), categoryId);
        adapter.save(buildExtracted(new BigDecimal("30.00"), LocalDate.of(2024, 1, 3), TransactionType.EXPENSE), categoryId);

        PageResult<Transaction> result = adapter.listPaginated(0, 2);

        assertThat(result.items()).hasSize(2);
        assertThat(result.total()).isEqualTo(3);
    }

    @Test
    void listByPeriodWithTypeShouldReturnOnlyMatchingTransactions() {
        adapter.save(buildExtracted(new BigDecimal("10.00"), LocalDate.of(2024, 6, 10), TransactionType.EXPENSE), categoryId);
        adapter.save(buildExtracted(new BigDecimal("20.00"), LocalDate.of(2024, 6, 20), TransactionType.INCOME), categoryId);
        adapter.save(buildExtracted(new BigDecimal("30.00"), LocalDate.of(2024, 7, 1), TransactionType.EXPENSE), categoryId);

        List<Transaction> result = adapter.listByPeriod(
            LocalDate.of(2024, 6, 1),
            LocalDate.of(2024, 6, 30),
            Optional.of(TransactionType.EXPENSE)
        );

        assertThat(result).hasSize(1);
        assertThat(result.get(0).transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(result.get(0).amount()).isEqualByComparingTo(new BigDecimal("10.00"));
    }

    @Test
    void listByPeriodWithoutTypeShouldReturnAllTransactionsInRange() {
        adapter.save(buildExtracted(new BigDecimal("10.00"), LocalDate.of(2024, 6, 5), TransactionType.EXPENSE), categoryId);
        adapter.save(buildExtracted(new BigDecimal("20.00"), LocalDate.of(2024, 6, 15), TransactionType.INCOME), categoryId);
        adapter.save(buildExtracted(new BigDecimal("30.00"), LocalDate.of(2024, 7, 1), TransactionType.EXPENSE), categoryId);

        List<Transaction> result = adapter.listByPeriod(
            LocalDate.of(2024, 6, 1),
            LocalDate.of(2024, 6, 30),
            Optional.empty()
        );

        assertThat(result).hasSize(2);
        assertThat(result).extracting(Transaction::transactionType)
            .containsExactlyInAnyOrder(TransactionType.EXPENSE, TransactionType.INCOME);
    }

    @Test
    void listRecentShouldReturnMostRecentTransactionsUpToLimit() {
        adapter.save(buildExtracted(new BigDecimal("10.00"), LocalDate.of(2024, 1, 1), TransactionType.EXPENSE), categoryId);
        adapter.save(buildExtracted(new BigDecimal("20.00"), LocalDate.of(2024, 1, 2), TransactionType.EXPENSE), categoryId);
        adapter.save(buildExtracted(new BigDecimal("30.00"), LocalDate.of(2024, 1, 3), TransactionType.EXPENSE), categoryId);

        List<Transaction> result = adapter.listRecent(2);

        assertThat(result).hasSize(2);
    }

    @Test
    void updateShouldChangeFieldsAndReturnUpdatedTransaction() {
        Transaction saved = adapter.save(defaultExtracted(), categoryId);
        TransactionUpdate update = new TransactionUpdate(
            new BigDecimal("99.99"),
            null,
            "Updated Establishment",
            null,
            null,
            null,
            null
        );

        Optional<Transaction> result = adapter.update(saved.id(), update);

        assertThat(result).isPresent();
        assertThat(result.get().amount()).isEqualByComparingTo(new BigDecimal("99.99"));
        assertThat(result.get().establishment()).isEqualTo("Updated Establishment");
    }

    @Test
    void updateShouldReturnEmptyWhenTransactionNotFound() {
        TransactionUpdate update = new TransactionUpdate(
            new BigDecimal("10.00"), null, null, null, null, null, null
        );

        Optional<Transaction> result = adapter.update(UUID.randomUUID(), update);

        assertThat(result).isEmpty();
    }

    @Test
    void updateShouldThrowCategoryNotFoundExceptionWhenCategoryIdIsInvalid() {
        Transaction saved = adapter.save(defaultExtracted(), categoryId);
        TransactionUpdate update = new TransactionUpdate(
            null, null, null, null, Integer.MAX_VALUE, null, null
        );

        assertThatThrownBy(() -> adapter.update(saved.id(), update))
            .isInstanceOf(CategoryNotFoundException.class);
    }

    @Test
    void deleteShouldRemoveTransactionAndReturnTrue() {
        Transaction saved = adapter.save(defaultExtracted(), categoryId);

        boolean result = adapter.delete(saved.id());

        assertThat(result).isTrue();
        assertThat(adapter.findById(saved.id())).isEmpty();
    }

    @Test
    void deleteShouldReturnFalseWhenTransactionNotFound() {
        boolean result = adapter.delete(UUID.randomUUID());

        assertThat(result).isFalse();
    }
}
