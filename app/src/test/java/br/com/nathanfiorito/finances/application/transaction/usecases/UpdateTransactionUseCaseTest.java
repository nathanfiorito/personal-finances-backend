package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.commands.UpdateTransactionCommand;
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

class UpdateTransactionUseCaseTest {

    private StubTransactionRepository repository;
    private UpdateTransactionUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new UpdateTransactionUseCase(repository);
    }

    private Transaction savedTransaction() {
        return new CreateTransactionUseCase(repository).execute(
            new CreateTransactionCommand(
                new BigDecimal("50.00"), LocalDate.now(),
                1, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
                "Store", null, null, 0.9
            )
        );
    }

    @Test
    void shouldReturnTransactionAfterUpdate() {
        Transaction saved = savedTransaction();

        Transaction result = useCase.execute(new UpdateTransactionCommand(
            saved.id(), new BigDecimal("75.00"), null,
            "New Store", null, null, null, null
        ));

        assertThat(result).isNotNull();
        assertThat(result.id()).isEqualTo(saved.id());
    }

    @Test
    void shouldThrowWhenTransactionNotFound() {
        assertThatThrownBy(() ->
            useCase.execute(new UpdateTransactionCommand(
                UUID.randomUUID(), null, null, "Updated", null, null, null, null
            ))
        ).isInstanceOf(TransactionNotFoundException.class);
    }
}
