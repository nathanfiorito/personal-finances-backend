package br.com.nathanfiorito.finances.infrastructure.card.adapter;

import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.infrastructure.BaseRepositoryIT;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Import;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@Import(CardRepositoryAdapter.class)
class CardRepositoryAdapterIT extends BaseRepositoryIT {

    @Autowired
    private CardRepositoryAdapter adapter;

    @Test
    void saveShouldPersistCardWithGeneratedIdAndActiveFlagTrue() {
        Card card = adapter.save("Nubank pessoal", "Nubank", "4532", 15, 25);

        assertThat(card.id()).isPositive();
        assertThat(card.alias()).isEqualTo("Nubank pessoal");
        assertThat(card.bank()).isEqualTo("Nubank");
        assertThat(card.lastFourDigits()).isEqualTo("4532");
        assertThat(card.closingDay()).isEqualTo(15);
        assertThat(card.dueDay()).isEqualTo(25);
        assertThat(card.active()).isTrue();
    }

    @Test
    void listActiveShouldReturnOnlyActiveCards() {
        adapter.save("Active Card", "Nubank", "1111", 10, 20);
        Card deactivated = adapter.save("Inactive Card", "Itaú", "2222", 5, 15);
        adapter.deactivate(deactivated.id());

        List<Card> result = adapter.listActive();

        assertThat(result).extracting(Card::alias).contains("Active Card");
        assertThat(result).extracting(Card::alias).doesNotContain("Inactive Card");
    }

    @Test
    void findByIdShouldReturnCardWhenFound() {
        Card saved = adapter.save("Inter", "Inter", "3333", 20, 1);

        Optional<Card> result = adapter.findById(saved.id());

        assertThat(result).isPresent();
        assertThat(result.get().alias()).isEqualTo("Inter");
    }

    @Test
    void findByIdShouldReturnEmptyWhenNotFound() {
        Optional<Card> result = adapter.findById(Integer.MAX_VALUE);

        assertThat(result).isEmpty();
    }

    @Test
    void updateShouldChangeFieldsAndReturnUpdatedCard() {
        Card saved = adapter.save("OldAlias", "OldBank", "0000", 1, 10);

        Optional<Card> result = adapter.update(saved.id(), "NewAlias", "NewBank", "9999", 25, 5);

        assertThat(result).isPresent();
        assertThat(result.get().alias()).isEqualTo("NewAlias");
        assertThat(result.get().bank()).isEqualTo("NewBank");
        assertThat(result.get().lastFourDigits()).isEqualTo("9999");
        assertThat(result.get().closingDay()).isEqualTo(25);
        assertThat(result.get().dueDay()).isEqualTo(5);
    }

    @Test
    void updateShouldReturnEmptyWhenCardNotFound() {
        Optional<Card> result = adapter.update(Integer.MAX_VALUE, "A", "B", "1234", 1, 1);

        assertThat(result).isEmpty();
    }

    @Test
    void deactivateShouldSetActiveFalseAndReturnTrue() {
        Card saved = adapter.save("ToDeactivate", "Bradesco", "5555", 10, 20);

        boolean result = adapter.deactivate(saved.id());

        assertThat(result).isTrue();
        Optional<Card> found = adapter.findById(saved.id());
        assertThat(found).isPresent();
        assertThat(found.get().active()).isFalse();
    }

    @Test
    void deactivateShouldReturnFalseWhenCardNotFound() {
        boolean result = adapter.deactivate(Integer.MAX_VALUE);

        assertThat(result).isFalse();
    }
}
