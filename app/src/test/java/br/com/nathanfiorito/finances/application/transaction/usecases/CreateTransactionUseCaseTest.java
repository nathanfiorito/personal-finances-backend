package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class CreateTransactionUseCaseTest {

    private StubTransactionRepository repository;
    private CreateTransactionUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new CreateTransactionUseCase(repository);
    }

    @Test
    void shouldReturnSavedTransaction() {
        var command = new CreateTransactionCommand(
            new BigDecimal("50.00"), LocalDate.of(2026, 1, 15),
            1, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
            "Test Store", null, null, 0.9
        );

        Transaction result = useCase.execute(command);

        assertThat(result.amount()).isEqualByComparingTo("50.00");
        assertThat(result.entryType()).isEqualTo("text");
        assertThat(result.transactionType()).isEqualTo(TransactionType.EXPENSE);
        assertThat(result.paymentMethod()).isEqualTo(PaymentMethod.DEBIT);
        assertThat(result.categoryId()).isEqualTo(1);
        assertThat(result.id()).isNotNull();
    }

    @Test
    void shouldPersistTransactionInRepository() {
        var command = new CreateTransactionCommand(
            new BigDecimal("100.00"), LocalDate.now(),
            2, "image", TransactionType.EXPENSE, PaymentMethod.CREDIT,
            "Supermarket", "Groceries", null, 0.95
        );

        useCase.execute(command);

        assertThat(repository.listPaginated(0, 10).total()).isEqualTo(1);
    }

    @Test
    void shouldSupportIncomeTransaction() {
        var command = new CreateTransactionCommand(
            new BigDecimal("5000.00"), LocalDate.now(),
            3, "text", TransactionType.INCOME, PaymentMethod.CREDIT,
            "Employer", null, null, 1.0
        );

        Transaction result = useCase.execute(command);

        assertThat(result.transactionType()).isEqualTo(TransactionType.INCOME);
    }
}
