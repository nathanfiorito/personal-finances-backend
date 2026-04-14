package br.com.nathanfiorito.finances.interfaces.rest.report.dto;

import br.com.nathanfiorito.finances.domain.transaction.records.SummaryItem;

import java.math.BigDecimal;

public record SummaryItemResponse(String category, BigDecimal total, int count) {

    public static SummaryItemResponse from(SummaryItem item) {
        return new SummaryItemResponse(item.category(), item.total(), item.count());
    }
}
