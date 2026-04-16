package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.commands.CreateCardCommand;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.stubs.StubCardRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class CreateCardUseCaseTest {

    private StubCardRepository repository;
    private CreateCardUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubCardRepository();
        useCase = new CreateCardUseCase(repository);
    }

    @Test
    void shouldCreateAndReturnCard() {
        Card result = useCase.execute(new CreateCardCommand("Nubank", "Nubank", "1234", 1, 10));

        assertThat(result.alias()).isEqualTo("Nubank");
        assertThat(result.bank()).isEqualTo("Nubank");
        assertThat(result.lastFourDigits()).isEqualTo("1234");
        assertThat(result.closingDay()).isEqualTo(1);
        assertThat(result.dueDay()).isEqualTo(10);
        assertThat(result.active()).isTrue();
        assertThat(result.id()).isGreaterThan(0);
    }

    @Test
    void shouldPersistCardInRepository() {
        useCase.execute(new CreateCardCommand("Inter", "Banco Inter", "5678", 5, 15));

        assertThat(repository.listActive()).hasSize(1);
    }
}
