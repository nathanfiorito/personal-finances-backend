package br.com.nathanfiorito.finances.interfaces.rest.report.dto;

import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyItem;

import java.math.BigDecimal;
import java.util.List;

public record MonthlyItemResponse(int month, BigDecimal total, List<MonthlyCategoryItemResponse> byCategory) {

    public static MonthlyItemResponse from(MonthlyItem item) {
        List<MonthlyCategoryItemResponse> categories = item.byCategory().stream()
            .map(MonthlyCategoryItemResponse::from)
            .toList();
        return new MonthlyItemResponse(item.month(), item.total(), categories);
    }
}
