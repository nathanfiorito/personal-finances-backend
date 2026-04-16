package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

public class StubCardRepository implements CardRepository {

    private final List<Card> cards = new ArrayList<>();
    private final AtomicInteger nextId = new AtomicInteger(1);

    @Override
    public Card save(String alias, String bank, String lastFourDigits, int closingDay, int dueDay) {
        Card card = new Card(nextId.getAndIncrement(), alias, bank, lastFourDigits, closingDay, dueDay, true, LocalDateTime.now());
        cards.add(card);
        return card;
    }

    @Override
    public List<Card> listActive() {
        return cards.stream().filter(Card::active).toList();
    }

    @Override
    public Optional<Card> findById(int id) {
        return cards.stream().filter(c -> c.id() == id).findFirst();
    }

    @Override
    public Optional<Card> update(int id, String alias, String bank, String lastFourDigits, int closingDay, int dueDay) {
        return cards.stream()
            .filter(c -> c.id() == id)
            .map(c -> new Card(c.id(), alias, bank, lastFourDigits, closingDay, dueDay, c.active(), c.createdAt()))
            .findFirst();
    }

    @Override
    public boolean deactivate(int id) {
        boolean found = cards.stream().anyMatch(c -> c.id() == id);
        if (found) {
            cards.replaceAll(c -> c.id() == id
                ? new Card(c.id(), c.alias(), c.bank(), c.lastFourDigits(), c.closingDay(), c.dueDay(), false, c.createdAt())
                : c);
        }
        return found;
    }
}
