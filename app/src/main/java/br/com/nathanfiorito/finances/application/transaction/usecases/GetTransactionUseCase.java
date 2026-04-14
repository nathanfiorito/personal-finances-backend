package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.GetTransactionQuery;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;

public class GetTransactionUseCase {

    private final TransactionRepository repository;

    public GetTransactionUseCase(TransactionRepository repository) {
        this.repository = repository;
    }

    public Transaction execute(GetTransactionQuery query) {
        return repository.findById(query.id())
            .orElseThrow(() -> new TransactionNotFoundException(query.id()));
    }
}
