package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.commands.ConfirmTransactionCommand;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.stubs.StubLlmPort;
import br.com.nathanfiorito.finances.stubs.StubNotifierPort;
import br.com.nathanfiorito.finances.stubs.StubPendingStatePort;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class ConfirmTransactionUseCaseTest {

    private static final long CHAT_ID = 111L;
    private static final long MESSAGE_ID = 42L;

    private StubTransactionRepository repo;
    private StubLlmPort llm;
    private StubPendingStatePort pendingState;
    private StubNotifierPort notifier;
    private ConfirmTransactionUseCase useCase;

    @BeforeEach
    void setUp() {
        repo = new StubTransactionRepository();
        llm = new StubLlmPort();
        pendingState = new StubPendingStatePort();
        notifier = new StubNotifierPort();
        useCase = new ConfirmTransactionUseCase(repo, llm, pendingState, notifier);
    }

    @Test
    void shouldEditMessageWithExpiredNoticeWhenNoPendingState() {
        useCase.execute(new ConfirmTransactionCommand(CHAT_ID, MESSAGE_ID, false));

        assertThat(notifier.editedMessages()).hasSize(1);
        assertThat(notifier.lastEdited().text()).contains("expirada");
    }

    @Test
    void shouldSaveTransactionAndClearStateOnConfirm() {
        pendingState.set(CHAT_ID, buildPendingTransaction());

        useCase.execute(new ConfirmTransactionCommand(CHAT_ID, MESSAGE_ID, false));

        assertThat(repo.listPaginated(0, 10).total()).isEqualTo(1);
        assertThat(pendingState.hasState(CHAT_ID)).isFalse();
        assertThat(notifier.lastSent().text()).contains("registrada");
    }

    @Test
    void shouldShowDuplicateWarningAndNotSave() {
        llm.setDuplicateResult(true);
        pendingState.set(CHAT_ID, buildPendingTransaction());

        useCase.execute(new ConfirmTransactionCommand(CHAT_ID, MESSAGE_ID, false));

        assertThat(repo.listPaginated(0, 10).total()).isEqualTo(0);
        assertThat(pendingState.hasState(CHAT_ID)).isTrue();
        assertThat(notifier.lastEdited().text()).contains("duplicidade");
    }

    @Test
    void shouldSaveEvenWhenDuplicateWhenSkipFlagSet() {
        llm.setDuplicateResult(true);
        pendingState.set(CHAT_ID, buildPendingTransaction());

        useCase.execute(new ConfirmTransactionCommand(CHAT_ID, MESSAGE_ID, true));

        assertThat(repo.listPaginated(0, 10).total()).isEqualTo(1);
    }

    private PendingTransaction buildPendingTransaction() {
        ExtractedTransaction extracted = new ExtractedTransaction(
            new BigDecimal("80.00"), LocalDate.now(),
            "Farmácia", "Remédios", null,
            "text", TransactionType.EXPENSE, PaymentMethod.DEBIT, 0.9
        );
        return PendingTransaction.create(extracted, "Saúde", 2, CHAT_ID, MESSAGE_ID);
    }
}
