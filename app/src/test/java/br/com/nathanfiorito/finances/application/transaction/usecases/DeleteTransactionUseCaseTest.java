package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.commands.DeleteTransactionCommand;
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

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.assertThatCode;

class DeleteTransactionUseCaseTest {

    private StubTransactionRepository repository;
    private DeleteTransactionUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new DeleteTransactionUseCase(repository);
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
    void shouldDeleteExistingTransaction() {
        Transaction saved = savedTransaction();

        assertThatCode(() ->
            useCase.execute(new DeleteTransactionCommand(saved.id()))
        ).doesNotThrowAnyException();
    }

    @Test
    void shouldThrowWhenTransactionNotFound() {
        assertThatThrownBy(() ->
            useCase.execute(new DeleteTransactionCommand(UUID.randomUUID()))
        ).isInstanceOf(TransactionNotFoundException.class);
    }
}
