package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.DeleteTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class DeleteTransactionUseCase {

    private final TransactionRepository repository;

    public void execute(DeleteTransactionCommand command) {
        log.info("Deleting transaction: id={}", command.id());
        boolean deleted = repository.delete(command.id());
        if (!deleted) {
            log.warn("Transaction not found for deletion: id={}", command.id());
            throw new TransactionNotFoundException(command.id());
        }
        log.info("Transaction deleted: id={}", command.id());
    }
}
