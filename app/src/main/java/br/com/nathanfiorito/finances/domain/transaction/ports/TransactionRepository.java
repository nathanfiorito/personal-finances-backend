package br.com.nathanfiorito.finances.domain.transaction.ports;

import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TransactionRepository {
    Transaction save(ExtractedTransaction extracted, int categoryId);
    Optional<Transaction> findById(UUID id);
    PageResult<Transaction> listPaginated(int page, int pageSize);
    List<Transaction> listByPeriod(LocalDate start, LocalDate end, TransactionType type);
    Optional<Transaction> update(UUID id, TransactionUpdate data);
    boolean delete(UUID id);
}
