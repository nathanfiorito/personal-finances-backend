package br.com.nathanfiorito.finances.domain.invoice.records;

public record DetectedCard(
    String lastFourDigits,
    Integer matchedCardId,
    String matchedCardAlias,
    String matchedCardBank
) {
    public static DetectedCard notDetected() {
        return new DetectedCard(null, null, null, null);
    }
}
