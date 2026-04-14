package br.com.nathanfiorito.finances.interfaces.rest.report.dto;

import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyCategoryItem;

import java.math.BigDecimal;

public record MonthlyCategoryItemResponse(String category, BigDecimal total) {

    public static MonthlyCategoryItemResponse from(MonthlyCategoryItem item) {
        return new MonthlyCategoryItemResponse(item.category(), item.total());
    }
}
