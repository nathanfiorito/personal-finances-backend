package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.domain.transaction.records.TransactionUpdate;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public class StubTransactionRepository implements TransactionRepository {

    private final List<Transaction> transactions = new ArrayList<>();

    @Override
    public Transaction save(ExtractedTransaction extracted, int categoryId) {
        Transaction saved = new Transaction(
            UUID.randomUUID(),
            extracted.amount(),
            extracted.date() != null ? extracted.date() : LocalDate.now(),
            extracted.establishment(),
            extracted.description(),
            categoryId,
            "Category " + categoryId,
            extracted.taxId(),
            extracted.entryType(),
            extracted.transactionType(),
            extracted.paymentMethod(),
            extracted.confidence(),
            LocalDateTime.now()
        );
        transactions.add(saved);
        return saved;
    }

    @Override
    public Optional<Transaction> findById(UUID id) {
        return transactions.stream().filter(t -> t.id().equals(id)).findFirst();
    }

    @Override
    public PageResult<Transaction> listPaginated(int page, int pageSize) {
        int fromIndex = Math.min(page * pageSize, transactions.size());
        int toIndex = Math.min(fromIndex + pageSize, transactions.size());
        return new PageResult<>(transactions.subList(fromIndex, toIndex), transactions.size());
    }

    @Override
    public List<Transaction> listByPeriod(LocalDate start, LocalDate end, Optional<TransactionType> type) {
        return transactions.stream()
            .filter(t -> !t.date().isBefore(start) && !t.date().isAfter(end))
            .filter(t -> type.isEmpty() || t.transactionType() == type.get())
            .toList();
    }

    @Override
    public List<Transaction> listRecent(int limit) {
        int fromIndex = Math.max(0, transactions.size() - limit);
        return new ArrayList<>(transactions.subList(fromIndex, transactions.size()));
    }

    @Override
    public Optional<Transaction> update(UUID id, TransactionUpdate data) {
        return transactions.stream().filter(t -> t.id().equals(id)).findFirst();
    }

    @Override
    public boolean delete(UUID id) {
        int before = transactions.size();
        transactions.removeIf(t -> t.id().equals(id));
        return transactions.size() < before;
    }
}
