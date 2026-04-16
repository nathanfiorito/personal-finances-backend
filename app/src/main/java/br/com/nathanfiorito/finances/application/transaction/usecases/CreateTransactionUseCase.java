package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class CreateTransactionUseCase {

    private final TransactionRepository repository;

    public Transaction execute(CreateTransactionCommand command) {
        log.info("Creating transaction: amount={}, establishment={}, categoryId={}, entryType={}",
            command.amount(), command.establishment(), command.categoryId(), command.entryType());
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
        Transaction saved = repository.save(extracted, command.categoryId());
        log.info("Transaction created: id={}, amount={}, category={}", saved.id(), saved.amount(), saved.category());
        return saved;
    }
}
