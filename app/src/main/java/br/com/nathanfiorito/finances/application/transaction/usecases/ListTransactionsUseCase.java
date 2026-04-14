package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.ListTransactionsQuery;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;

public class ListTransactionsUseCase {

    private final TransactionRepository repository;

    public ListTransactionsUseCase(TransactionRepository repository) {
        this.repository = repository;
    }

    public PageResult<Transaction> execute(ListTransactionsQuery query) {
        return repository.listPaginated(query.page(), query.pageSize());
    }
}
