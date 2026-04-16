package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class GetCardUseCase {

    private final CardRepository repository;

    public Card execute(int id) {
        log.debug("Getting card: id={}", id);
        Card card = repository.findById(id)
            .orElseThrow(() -> {
                log.warn("Card not found: id={}", id);
                return new CardNotFoundException(id);
            });
        log.debug("Found card: id={}, alias={}", card.id(), card.alias());
        return card;
    }
}
