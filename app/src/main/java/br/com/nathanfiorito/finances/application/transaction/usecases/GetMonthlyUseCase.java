package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.GetMonthlyQuery;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyCategoryItem;
import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyItem;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;

@Slf4j
@RequiredArgsConstructor
public class GetMonthlyUseCase {

    private final TransactionRepository repository;

    public List<MonthlyItem> execute(GetMonthlyQuery query) {
        log.debug("Generating monthly report: year={}", query.year());
        LocalDate start = LocalDate.of(query.year(), 1, 1);
        LocalDate end   = LocalDate.of(query.year(), 12, 31);

        List<Transaction> transactions = repository.listByPeriod(start, end, Optional.empty());

        // month → (category → total)
        Map<Integer, Map<String, BigDecimal>> byMonth = new TreeMap<>();
        for (Transaction tx : transactions) {
            int month = tx.date().getMonthValue();
            String category = tx.category() != null ? tx.category() : "Sem categoria";
            byMonth
                .computeIfAbsent(month, k -> new LinkedHashMap<>())
                .merge(category, tx.amount(), BigDecimal::add);
        }

        List<MonthlyItem> result = new ArrayList<>();
        for (Map.Entry<Integer, Map<String, BigDecimal>> entry : byMonth.entrySet()) {
            List<MonthlyCategoryItem> categories = entry.getValue().entrySet().stream()
                .map(e -> new MonthlyCategoryItem(e.getKey(), e.getValue()))
                .sorted(Comparator.comparing(MonthlyCategoryItem::category))
                .toList();
            BigDecimal total = categories.stream()
                .map(MonthlyCategoryItem::total)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
            result.add(new MonthlyItem(entry.getKey(), total, categories));
        }
        log.debug("Monthly report generated: year={}, months={}, transactions={}", query.year(), result.size(), transactions.size());
        return result;
    }
}
