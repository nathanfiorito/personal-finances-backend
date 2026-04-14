package br.com.nathanfiorito.finances.domain.transaction.ports;

import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;

import java.util.List;

public interface LlmPort {
    ExtractedTransaction extractTransaction(String content, String entryType);
    boolean isDuplicate(ExtractedTransaction extracted, List<Transaction> recentTransactions);
}
