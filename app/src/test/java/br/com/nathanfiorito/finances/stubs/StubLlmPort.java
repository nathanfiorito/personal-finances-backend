package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public class StubLlmPort implements LlmPort {

    private boolean duplicateResult = false;
    private String categorizeResult = "Alimentação";

    public void setDuplicateResult(boolean duplicate) {
        this.duplicateResult = duplicate;
    }

    public void setCategorizeResult(String category) {
        this.categorizeResult = category;
    }

    @Override
    public ExtractedTransaction extractTransaction(String content, String entryType) {
        return new ExtractedTransaction(
            new BigDecimal("50.00"),
            LocalDate.of(2026, 1, 15),
            "Supermercado Teste",
            "Compras do mês",
            null,
            entryType,
            TransactionType.EXPENSE,
            PaymentMethod.DEBIT,
            0.95
        );
    }

    @Override
    public boolean isDuplicate(ExtractedTransaction extracted, List<Transaction> recentTransactions) {
        return duplicateResult;
    }

    @Override
    public String categorize(ExtractedTransaction extracted, List<String> categoryNames) {
        if (categoryNames.contains(categorizeResult)) return categorizeResult;
        return categoryNames.isEmpty() ? "Outros" : categoryNames.get(0);
    }
}
