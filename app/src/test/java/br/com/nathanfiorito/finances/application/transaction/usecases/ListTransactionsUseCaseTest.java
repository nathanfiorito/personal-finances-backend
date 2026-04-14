package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.queries.ListTransactionsQuery;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class ListTransactionsUseCaseTest {

    private StubTransactionRepository repository;
    private ListTransactionsUseCase useCase;
    private CreateTransactionUseCase createUseCase;

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new ListTransactionsUseCase(repository);
        createUseCase = new CreateTransactionUseCase(repository);
    }

    private void createTransactions(int count) {
        for (int i = 0; i < count; i++) {
            createUseCase.execute(new CreateTransactionCommand(
                new BigDecimal("10.00"), LocalDate.now(),
                1, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
                "Store " + i, null, null, 0.9
            ));
        }
    }

    @Test
    void shouldReturnAllTransactions() {
        createTransactions(3);

        PageResult<Transaction> result = useCase.execute(new ListTransactionsQuery(0, 20));

        assertThat(result.total()).isEqualTo(3);
        assertThat(result.items()).hasSize(3);
    }

    @Test
    void shouldReturnEmptyWhenNoTransactions() {
        PageResult<Transaction> result = useCase.execute(new ListTransactionsQuery(0, 20));

        assertThat(result.total()).isEqualTo(0);
        assertThat(result.items()).isEmpty();
    }

    @Test
    void shouldCapPageSizeAt100() {
        ListTransactionsQuery query = new ListTransactionsQuery(0, 999);

        assertThat(query.pageSize()).isEqualTo(100);
    }

    @Test
    void shouldUseDefaultPageSizeWhenConstructedWithNoArgs() {
        ListTransactionsQuery query = new ListTransactionsQuery();

        assertThat(query.page()).isEqualTo(0);
        assertThat(query.pageSize()).isEqualTo(20);
    }
}
