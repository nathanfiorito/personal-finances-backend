package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.List;

@Slf4j
@RequiredArgsConstructor
public class ListCardsUseCase {

    private final CardRepository repository;

    public List<Card> execute() {
        log.debug("Listing active cards");
        List<Card> cards = repository.listActive();
        log.debug("Listed {} active cards", cards.size());
        return cards;
    }
}
