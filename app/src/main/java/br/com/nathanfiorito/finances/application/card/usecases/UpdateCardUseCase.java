package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.commands.UpdateCardCommand;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class UpdateCardUseCase {

    private final CardRepository repository;

    public Card execute(UpdateCardCommand command) {
        log.info("Updating card: id={}, alias={}, bank={}", command.id(), command.alias(), command.bank());
        Card updated = repository.update(command.id(), command.alias(), command.bank(), command.lastFourDigits(), command.closingDay(), command.dueDay())
            .orElseThrow(() -> {
                log.warn("Card not found for update: id={}", command.id());
                return new CardNotFoundException(command.id());
            });
        log.info("Card updated: id={}, alias={}", updated.id(), updated.alias());
        return updated;
    }
}
