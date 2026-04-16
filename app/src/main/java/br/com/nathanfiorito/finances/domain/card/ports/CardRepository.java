package br.com.nathanfiorito.finances.domain.card.ports;

import br.com.nathanfiorito.finances.domain.card.records.Card;
import java.util.List;
import java.util.Optional;

public interface CardRepository {
    Card save(String alias, String bank, String lastFourDigits, int closingDay, int dueDay);
    List<Card> listActive();
    Optional<Card> findById(int id);
    Optional<Card> update(int id, String alias, String bank, String lastFourDigits, int closingDay, int dueDay);
    boolean deactivate(int id);
}
