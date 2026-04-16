package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.UpdateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class UpdateTransactionUseCase {

    private final TransactionRepository repository;

    public Transaction execute(UpdateTransactionCommand command) {
        log.info("Updating transaction: id={}", command.id());
        repository.findById(command.id())
            .orElseThrow(() -> {
                log.warn("Transaction not found for update: id={}", command.id());
                return new TransactionNotFoundException(command.id());
            });

        TransactionUpdate update = new TransactionUpdate(
            command.amount(),
            command.date(),
            command.establishment(),
            command.description(),
            command.categoryId(),
            command.paymentMethod(),
            command.transactionType()
        );

        Transaction updated = repository.update(command.id(), update)
            .orElseThrow(() -> new TransactionNotFoundException(command.id()));
        log.info("Transaction updated: id={}, amount={}, category={}", updated.id(), updated.amount(), updated.category());
        return updated;
    }
}
