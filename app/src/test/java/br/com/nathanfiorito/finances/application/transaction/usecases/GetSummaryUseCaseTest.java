package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.queries.GetSummaryQuery;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.SummaryItem;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

class GetSummaryUseCaseTest {

    private StubTransactionRepository repository;
    private GetSummaryUseCase useCase;
    private CreateTransactionUseCase createUseCase;

    private static final LocalDate START = LocalDate.of(2025, 1, 1);
    private static final LocalDate END   = LocalDate.of(2025, 1, 31);

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new GetSummaryUseCase(repository);
        createUseCase = new CreateTransactionUseCase(repository);
    }

    private void create(BigDecimal amount, int categoryId, TransactionType type, LocalDate date) {
        createUseCase.execute(new CreateTransactionCommand(
            amount, date, categoryId, "text", type, PaymentMethod.DEBIT,
            "Store", null, null, 0.9
        ));
    }

    @Test
    void shouldAggregateTotalAndCountPerCategory() {
        create(new BigDecimal("50.00"), 1, TransactionType.EXPENSE, LocalDate.of(2025, 1, 10));
        create(new BigDecimal("30.00"), 1, TransactionType.EXPENSE, LocalDate.of(2025, 1, 15));
        create(new BigDecimal("20.00"), 2, TransactionType.EXPENSE, LocalDate.of(2025, 1, 20));

        List<SummaryItem> result = useCase.execute(new GetSummaryQuery(START, END, Optional.empty()));

        assertThat(result).hasSize(2);
        SummaryItem cat1 = result.stream().filter(s -> s.count() == 2).findFirst().orElseThrow();
        assertThat(cat1.total()).isEqualByComparingTo("80.00");
        SummaryItem cat2 = result.stream().filter(s -> s.count() == 1).findFirst().orElseThrow();
        assertThat(cat2.total()).isEqualByComparingTo("20.00");
    }

    @Test
    void shouldFilterByTransactionType() {
        create(new BigDecimal("100.00"), 1, TransactionType.EXPENSE, LocalDate.of(2025, 1, 10));
        create(new BigDecimal("200.00"), 1, TransactionType.INCOME,  LocalDate.of(2025, 1, 10));

        List<SummaryItem> expenses = useCase.execute(
            new GetSummaryQuery(START, END, Optional.of(TransactionType.EXPENSE)));

        assertThat(expenses).hasSize(1);
        assertThat(expenses.get(0).total()).isEqualByComparingTo("100.00");
    }

    @Test
    void shouldReturnEmptyWhenNoTransactionsInPeriod() {
        create(new BigDecimal("50.00"), 1, TransactionType.EXPENSE, LocalDate.of(2024, 12, 31));

        List<SummaryItem> result = useCase.execute(new GetSummaryQuery(START, END, Optional.empty()));

        assertThat(result).isEmpty();
    }

    @Test
    void shouldReturnResultsSortedAlphabetically() {
        create(new BigDecimal("10.00"), 3, TransactionType.EXPENSE, LocalDate.of(2025, 1, 5));
        create(new BigDecimal("10.00"), 1, TransactionType.EXPENSE, LocalDate.of(2025, 1, 5));

        List<SummaryItem> result = useCase.execute(new GetSummaryQuery(START, END, Optional.empty()));

        assertThat(result).isSortedAccordingTo(
            (a, b) -> a.category().compareToIgnoreCase(b.category()));
    }
}
