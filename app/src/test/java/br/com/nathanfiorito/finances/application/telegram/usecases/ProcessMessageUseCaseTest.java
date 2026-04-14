package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.commands.ProcessMessageCommand;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import br.com.nathanfiorito.finances.stubs.StubLlmPort;
import br.com.nathanfiorito.finances.stubs.StubNotifierPort;
import br.com.nathanfiorito.finances.stubs.StubPendingStatePort;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ProcessMessageUseCaseTest {

    private static final long CHAT_ID = 123456L;

    private StubLlmPort llm;
    private StubCategoryRepository categoryRepo;
    private StubPendingStatePort pendingState;
    private StubNotifierPort notifier;
    private ProcessMessageUseCase useCase;

    @BeforeEach
    void setUp() {
        llm = new StubLlmPort();
        categoryRepo = new StubCategoryRepository();
        pendingState = new StubPendingStatePort();
        notifier = new StubNotifierPort();
        useCase = new ProcessMessageUseCase(llm, categoryRepo, pendingState, notifier);
    }

    @Test
    void shouldExtractAndStoreTransactionAsPending() {
        categoryRepo.save("Alimentação");
        llm.setCategorizeResult("Alimentação");

        useCase.execute(new ProcessMessageCommand(CHAT_ID, "text", "Comprei pão por R$10", null));

        assertThat(pendingState.hasState(CHAT_ID)).isTrue();
    }

    @Test
    void shouldSendConfirmationMessageWithButtons() {
        categoryRepo.save("Alimentação");
        llm.setCategorizeResult("Alimentação");

        useCase.execute(new ProcessMessageCommand(CHAT_ID, "text", "Comprei pão por R$10", null));

        assertThat(notifier.sentMessages()).hasSize(1);
        StubNotifierPort.SentMessage msg = notifier.lastSent();
        assertThat(msg.chatId()).isEqualTo(CHAT_ID);
        assertThat(msg.text()).contains("Supermercado Teste");
        assertThat(msg.text()).contains("Alimentação");
        assertThat(msg.buttons()).isNotEmpty();
    }

    @Test
    void shouldFallbackToFirstCategoryWhenLlmReturnsUnknown() {
        categoryRepo.save("Transporte");
        llm.setCategorizeResult("Categoria Inexistente");

        useCase.execute(new ProcessMessageCommand(CHAT_ID, "text", "Uber R$25", null));

        assertThat(pendingState.hasState(CHAT_ID)).isTrue();
        assertThat(notifier.lastSent().text()).contains("Transporte");
    }

    @Test
    void shouldIncludeConfirmAndCancelButtons() {
        categoryRepo.save("Outros");

        useCase.execute(new ProcessMessageCommand(CHAT_ID, "image", "base64data", 99L));

        var buttons = notifier.lastSent().buttons();
        assertThat(buttons.get(0)).anyMatch(b -> b.callbackData().equals("confirm"));
        assertThat(buttons.get(0)).anyMatch(b -> b.callbackData().equals("cancel"));
        assertThat(buttons.get(1)).anyMatch(b -> b.callbackData().equals("edit_category"));
    }
}
