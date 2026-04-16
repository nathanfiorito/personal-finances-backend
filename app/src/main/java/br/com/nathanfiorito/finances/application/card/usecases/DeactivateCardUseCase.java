package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.commands.DeactivateCardCommand;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class DeactivateCardUseCase {

    private final CardRepository repository;

    public void execute(DeactivateCardCommand command) {
        log.info("Deactivating card: id={}", command.id());
        boolean deactivated = repository.deactivate(command.id());
        if (!deactivated) {
            log.warn("Card not found for deactivation: id={}", command.id());
            throw new CardNotFoundException(command.id());
        }
        log.info("Card deactivated: id={}", command.id());
    }
}
