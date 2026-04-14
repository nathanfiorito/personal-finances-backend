package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.UpdateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;

public class UpdateTransactionUseCase {

    private final TransactionRepository repository;

    public UpdateTransactionUseCase(TransactionRepository repository) {
        this.repository = repository;
    }

    public Transaction execute(UpdateTransactionCommand command) {
        repository.findById(command.id())
            .orElseThrow(() -> new TransactionNotFoundException(command.id()));

        TransactionUpdate update = new TransactionUpdate(
            command.amount(),
            command.date(),
            command.establishment(),
            command.description(),
            command.categoryId(),
            command.paymentMethod(),
            command.transactionType()
        );

        return repository.update(command.id(), update)
            .orElseThrow(() -> new TransactionNotFoundException(command.id()));
    }
}
