package br.com.nathanfiorito.finances.domain.transaction.records;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;

public record ExtractedTransaction(
    BigDecimal amount,
    LocalDate date,
    String establishment,
    String description,
    String taxId,
    String entryType,
    TransactionType transactionType,
    PaymentMethod paymentMethod,
    double confidence
) {
    public ExtractedTransaction {
        Objects.requireNonNull(amount, "amount must not be null");
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        if (amount.compareTo(new BigDecimal("999999.99")) > 0) {
            throw new IllegalArgumentException("Amount exceeds reasonable limit of 999,999.99");
        }
        taxId = formatTaxId(taxId);
    }

    private static String formatTaxId(String taxId) {
        if (taxId == null) return null;
        String digits = taxId.replaceAll("\\D", "");
        if (digits.length() == 14) {
            return String.format("%s.%s.%s/%s-%s",
                digits.substring(0, 2),
                digits.substring(2, 5),
                digits.substring(5, 8),
                digits.substring(8, 12),
                digits.substring(12));
        }
        return taxId;
    }
}
