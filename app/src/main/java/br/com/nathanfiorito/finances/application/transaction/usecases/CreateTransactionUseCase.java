package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class CreateTransactionUseCase {

    private final TransactionRepository repository;

    public Transaction execute(CreateTransactionCommand command) {
        ExtractedTransaction extracted = new ExtractedTransaction(
            command.amount(),
            command.date(),
            command.establishment(),
            command.description(),
            command.taxId(),
            command.entryType(),
            command.transactionType(),
            command.paymentMethod(),
            command.confidence()
        );
        return repository.save(extracted, command.categoryId());
    }
}
