package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.commands.CreateCardCommand;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class CreateCardUseCase {

    private final CardRepository repository;

    public Card execute(CreateCardCommand command) {
        log.info("Creating card: alias={}, bank={}, lastFourDigits={}", command.alias(), command.bank(), command.lastFourDigits());
        Card created = repository.save(command.alias(), command.bank(), command.lastFourDigits(), command.closingDay(), command.dueDay());
        log.info("Card created: id={}, alias={}", created.id(), created.alias());
        return created;
    }
}
