package br.com.nathanfiorito.finances.domain.telegram.records;

import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;

import java.time.Duration;
import java.time.Instant;

public record PendingTransaction(
    ExtractedTransaction extracted,
    String category,
    int categoryId,
    long chatId,
    Long messageId,
    Instant expiresAt
) {
    private static final Duration TTL = Duration.ofMinutes(10);

    public static PendingTransaction create(
        ExtractedTransaction extracted,
        String category,
        int categoryId,
        long chatId,
        Long messageId
    ) {
        return new PendingTransaction(
            extracted, category, categoryId, chatId, messageId,
            Instant.now().plus(TTL)
        );
    }

    public boolean isExpired() {
        return Instant.now().isAfter(expiresAt);
    }
}
