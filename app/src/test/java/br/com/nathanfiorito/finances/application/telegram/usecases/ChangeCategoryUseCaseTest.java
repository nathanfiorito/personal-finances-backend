package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.commands.ChangeCategoryCommand;
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

class ChangeCategoryUseCaseTest {

    private static final long CHAT_ID = 333L;
    private static final long MESSAGE_ID = 20L;

    private StubPendingStatePort pendingState;
    private StubNotifierPort notifier;
    private ChangeCategoryUseCase useCase;

    @BeforeEach
    void setUp() {
        pendingState = new StubPendingStatePort();
        notifier = new StubNotifierPort();
        useCase = new ChangeCategoryUseCase(pendingState, notifier);
    }

    @Test
    void shouldUpdateCategoryAndReRenderMessage() {
        pendingState.set(CHAT_ID, buildPendingTransaction("Alimentação", 1));

        useCase.execute(new ChangeCategoryCommand(CHAT_ID, MESSAGE_ID, "Transporte", 5));

        assertThat(notifier.editedMessages()).hasSize(1);
        assertThat(notifier.lastEdited().text()).contains("Transporte");
        assertThat(notifier.lastEdited().text()).doesNotContain("Alimentação");
    }

    @Test
    void shouldShowExpiredMessageWhenNoPendingState() {
        useCase.execute(new ChangeCategoryCommand(CHAT_ID, MESSAGE_ID, "Saúde", 3));

        assertThat(notifier.lastEdited().text()).contains("expirada");
    }

    @Test
    void shouldKeepConfirmAndCancelButtonsAfterCategoryChange() {
        pendingState.set(CHAT_ID, buildPendingTransaction("Outros", 1));

        useCase.execute(new ChangeCategoryCommand(CHAT_ID, MESSAGE_ID, "Lazer", 7));

        var buttons = notifier.lastEdited().buttons();
        assertThat(buttons).isNotEmpty();
        assertThat(buttons.get(0)).anyMatch(b -> b.callbackData().equals("confirm"));
        assertThat(buttons.get(0)).anyMatch(b -> b.callbackData().equals("cancel"));
    }

    private PendingTransaction buildPendingTransaction(String category, int categoryId) {
        ExtractedTransaction extracted = new ExtractedTransaction(
            new BigDecimal("150.00"), LocalDate.now(),
            "Loja X", "Produto Y", null,
            "text", TransactionType.EXPENSE, PaymentMethod.CREDIT, 0.85
        );
        return PendingTransaction.create(extracted, category, categoryId, CHAT_ID, MESSAGE_ID);
    }
}
