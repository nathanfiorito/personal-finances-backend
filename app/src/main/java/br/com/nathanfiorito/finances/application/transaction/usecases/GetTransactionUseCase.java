package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.GetTransactionQuery;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class GetTransactionUseCase {

    private final TransactionRepository repository;

    public Transaction execute(GetTransactionQuery query) {
        log.debug("Fetching transaction: id={}", query.id());
        return repository.findById(query.id())
            .orElseThrow(() -> {
                log.warn("Transaction not found: id={}", query.id());
                return new TransactionNotFoundException(query.id());
            });
    }
}
