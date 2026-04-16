package br.com.nathanfiorito.finances.interfaces.rest.invoice.dto;

import br.com.nathanfiorito.finances.domain.card.records.Invoice;
import br.com.nathanfiorito.finances.interfaces.rest.transaction.dto.TransactionResponse;

import java.util.List;

public record InvoiceResponse(
    int cardId,
    String periodStart,
    String periodEnd,
    String closingDate,
    String dueDate,
    String total,
    List<TransactionResponse> transactions
) {
    public static InvoiceResponse from(Invoice invoice) {
        List<TransactionResponse> txResponses = invoice.transactions().stream()
            .map(TransactionResponse::from)
            .toList();
        return new InvoiceResponse(
            invoice.cardId(),
            invoice.periodStart().toString(),
            invoice.periodEnd().toString(),
            invoice.closingDate().toString(),
            invoice.dueDate().toString(),
            invoice.total().toPlainString(),
            txResponses
        );
    }
}
