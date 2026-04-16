package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.ListTransactionsQuery;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class ListTransactionsUseCase {

    private final TransactionRepository repository;

    public PageResult<Transaction> execute(ListTransactionsQuery query) {
        log.debug("Listing transactions: page={}, pageSize={}", query.page(), query.pageSize());
        PageResult<Transaction> result = repository.listPaginated(query.page(), query.pageSize());
        log.debug("Listed transactions: count={}, total={}", result.items().size(), result.total());
        return result;
    }
}
