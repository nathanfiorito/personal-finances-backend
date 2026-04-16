package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.queries.GetMonthlyQuery;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyItem;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class GetMonthlyUseCaseTest {

    private StubTransactionRepository repository;
    private GetMonthlyUseCase useCase;
    private CreateTransactionUseCase createUseCase;

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new GetMonthlyUseCase(repository);
        createUseCase = new CreateTransactionUseCase(repository);
    }

    private void create(BigDecimal amount, int categoryId, LocalDate date) {
        createUseCase.execute(new CreateTransactionCommand(
            amount, date, categoryId, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
            "Store", null, null, 0.9, null
        ));
    }

    @Test
    void shouldGroupTransactionsByMonth() {
        create(new BigDecimal("100.00"), 1, LocalDate.of(2025, 1, 10));
        create(new BigDecimal("200.00"), 1, LocalDate.of(2025, 3, 15));

        List<MonthlyItem> result = useCase.execute(new GetMonthlyQuery(2025));

        assertThat(result).hasSize(2);
        assertThat(result.get(0).month()).isEqualTo(1);
        assertThat(result.get(1).month()).isEqualTo(3);
    }

    @Test
    void shouldSumTotalsWithinSameMonth() {
        create(new BigDecimal("50.00"), 1, LocalDate.of(2025, 2, 1));
        create(new BigDecimal("70.00"), 1, LocalDate.of(2025, 2, 15));

        List<MonthlyItem> result = useCase.execute(new GetMonthlyQuery(2025));

        assertThat(result).hasSize(1);
        assertThat(result.get(0).total()).isEqualByComparingTo("120.00");
    }

    @Test
    void shouldExcludeTransactionsOutsideYear() {
        create(new BigDecimal("100.00"), 1, LocalDate.of(2024, 12, 31));
        create(new BigDecimal("50.00"),  1, LocalDate.of(2025, 1, 1));

        List<MonthlyItem> result = useCase.execute(new GetMonthlyQuery(2025));

        assertThat(result).hasSize(1);
        assertThat(result.get(0).month()).isEqualTo(1);
    }

    @Test
    void shouldReturnEmptyForYearWithNoTransactions() {
        create(new BigDecimal("100.00"), 1, LocalDate.of(2025, 6, 1));

        List<MonthlyItem> result = useCase.execute(new GetMonthlyQuery(2024));

        assertThat(result).isEmpty();
    }

    @Test
    void shouldGroupByCategoryWithinMonth() {
        create(new BigDecimal("40.00"), 1, LocalDate.of(2025, 4, 10));
        create(new BigDecimal("60.00"), 2, LocalDate.of(2025, 4, 20));

        List<MonthlyItem> result = useCase.execute(new GetMonthlyQuery(2025));

        assertThat(result).hasSize(1);
        assertThat(result.get(0).byCategory()).hasSize(2);
    }
}
