package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.queries.ExportCsvQuery;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;

@Slf4j
@RequiredArgsConstructor
public class ExportCsvUseCase {

    private static final String BOM = "\uFEFF";
    private static final String HEADER = "date,amount,establishment,category,description,tax_id,entry_type,transaction_type\n";

    private final TransactionRepository repository;

    public byte[] execute(ExportCsvQuery query) {
        log.info("Exporting CSV: start={}, end={}", query.start(), query.end());
        List<Transaction> transactions = repository.listByPeriod(query.start(), query.end(), Optional.empty());

        StringBuilder csv = new StringBuilder(BOM).append(HEADER);
        for (Transaction tx : transactions) {
            csv.append(tx.date()).append(',')
               .append(tx.amount().toPlainString()).append(',')
               .append(escape(tx.establishment())).append(',')
               .append(escape(tx.category())).append(',')
               .append(escape(tx.description())).append(',')
               .append(escape(tx.taxId())).append(',')
               .append(escape(tx.entryType())).append(',')
               .append(tx.transactionType() != null ? tx.transactionType().name().toLowerCase() : "")
               .append('\n');
        }
        log.info("CSV exported: transactionCount={}, start={}, end={}", transactions.size(), query.start(), query.end());
        return csv.toString().getBytes(StandardCharsets.UTF_8);
    }

    private String escape(String value) {
        if (value == null) return "";
        if (value.contains(",") || value.contains("\"") || value.contains("\n")) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }
}
