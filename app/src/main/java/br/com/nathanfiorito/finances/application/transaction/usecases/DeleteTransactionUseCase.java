package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.DeleteTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class DeleteTransactionUseCase {

    private final TransactionRepository repository;

    public void execute(DeleteTransactionCommand command) {
        boolean deleted = repository.delete(command.id());
        if (!deleted) {
            throw new TransactionNotFoundException(command.id());
        }
    }
}
