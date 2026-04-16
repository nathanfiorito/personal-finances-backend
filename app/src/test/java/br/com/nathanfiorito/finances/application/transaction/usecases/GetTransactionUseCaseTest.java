package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.queries.GetTransactionQuery;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class GetTransactionUseCaseTest {

    private StubTransactionRepository repository;
    private GetTransactionUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new GetTransactionUseCase(repository);
    }

    private Transaction savedTransaction() {
        return new CreateTransactionUseCase(repository).execute(
            new CreateTransactionCommand(
                new BigDecimal("75.00"), LocalDate.now(),
                1, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
                "Store", null, null, 0.8, null
            )
        );
    }

    @Test
    void shouldReturnTransactionWhenFound() {
        Transaction saved = savedTransaction();

        Transaction result = useCase.execute(new GetTransactionQuery(saved.id()));

        assertThat(result.id()).isEqualTo(saved.id());
        assertThat(result.amount()).isEqualByComparingTo("75.00");
    }

    @Test
    void shouldThrowWhenTransactionNotFound() {
        assertThatThrownBy(() ->
            useCase.execute(new GetTransactionQuery(UUID.randomUUID()))
        ).isInstanceOf(TransactionNotFoundException.class)
         .hasMessageContaining("Transaction not found");
    }
}
