package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.GetSummaryQuery;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.SummaryItem;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;

import java.math.BigDecimal;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RequiredArgsConstructor
public class GetSummaryUseCase {

    private final TransactionRepository repository;

    public List<SummaryItem> execute(GetSummaryQuery query) {
        List<Transaction> transactions = repository.listByPeriod(query.start(), query.end(), query.type());

        Map<String, BigDecimal[]> aggregated = new LinkedHashMap<>();
        for (Transaction tx : transactions) {
            String category = tx.category() != null ? tx.category() : "Sem categoria";
            aggregated.computeIfAbsent(category, k -> new BigDecimal[]{BigDecimal.ZERO, BigDecimal.ZERO});
            aggregated.get(category)[0] = aggregated.get(category)[0].add(tx.amount());
            aggregated.get(category)[1] = aggregated.get(category)[1].add(BigDecimal.ONE);
        }

        return aggregated.entrySet().stream()
            .map(e -> new SummaryItem(e.getKey(), e.getValue()[0], e.getValue()[1].intValue()))
            .sorted(Comparator.comparing(SummaryItem::category))
            .toList();
    }
}
