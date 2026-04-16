package br.com.nathanfiorito.finances.infrastructure.card.adapter;

import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.infrastructure.card.entity.CardEntity;
import br.com.nathanfiorito.finances.infrastructure.card.mapper.CardMapper;
import br.com.nathanfiorito.finances.infrastructure.card.repository.JpaCardRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class CardRepositoryAdapter implements CardRepository {

    private final JpaCardRepository jpa;

    @Override
    public Card save(String alias, String bank, String lastFourDigits, int closingDay, int dueDay) {
        CardEntity entity = new CardEntity();
        entity.setAlias(alias);
        entity.setBank(bank);
        entity.setLastFourDigits(lastFourDigits);
        entity.setClosingDay(closingDay);
        entity.setDueDay(dueDay);
        entity.setActive(true);
        return CardMapper.toDomain(jpa.save(entity));
    }

    @Override
    public List<Card> listActive() {
        return jpa.findByActiveTrue().stream().map(CardMapper::toDomain).toList();
    }

    @Override
    public Optional<Card> findById(int id) {
        return jpa.findById(id).map(CardMapper::toDomain);
    }

    @Override
    public Optional<Card> update(int id, String alias, String bank, String lastFourDigits, int closingDay, int dueDay) {
        return jpa.findById(id).map(entity -> {
            entity.setAlias(alias);
            entity.setBank(bank);
            entity.setLastFourDigits(lastFourDigits);
            entity.setClosingDay(closingDay);
            entity.setDueDay(dueDay);
            return CardMapper.toDomain(jpa.save(entity));
        });
    }

    @Override
    public boolean deactivate(int id) {
        return jpa.findById(id).map(entity -> {
            entity.setActive(false);
            jpa.save(entity);
            return true;
        }).orElse(false);
    }
}
