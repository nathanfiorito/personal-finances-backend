package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.commands.CancelTransactionCommand;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.stubs.StubNotifierPort;
import br.com.nathanfiorito.finances.stubs.StubPendingStatePort;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class CancelTransactionUseCaseTest {

    private static final long CHAT_ID = 222L;
    private static final long MESSAGE_ID = 10L;

    private StubPendingStatePort pendingState;
    private StubNotifierPort notifier;
    private CancelTransactionUseCase useCase;

    @BeforeEach
    void setUp() {
        pendingState = new StubPendingStatePort();
        notifier = new StubNotifierPort();
        useCase = new CancelTransactionUseCase(pendingState, notifier);
    }

    @Test
    void shouldClearPendingStateAndEditMessage() {
        pendingState.set(CHAT_ID, buildPendingTransaction());

        useCase.execute(new CancelTransactionCommand(CHAT_ID, MESSAGE_ID));

        assertThat(pendingState.hasState(CHAT_ID)).isFalse();
        assertThat(notifier.lastEdited().text()).contains("cancelada");
    }

    @Test
    void shouldEditMessageEvenWithNoPendingState() {
        useCase.execute(new CancelTransactionCommand(CHAT_ID, MESSAGE_ID));

        assertThat(notifier.editedMessages()).hasSize(1);
        assertThat(notifier.lastEdited().chatId()).isEqualTo(CHAT_ID);
    }

    private PendingTransaction buildPendingTransaction() {
        ExtractedTransaction extracted = new ExtractedTransaction(
            new BigDecimal("30.00"), LocalDate.now(),
            "Padaria", null, null,
            "text", TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.8
        );
        return PendingTransaction.create(extracted, "Alimentação", 1, CHAT_ID, MESSAGE_ID);
    }
}
