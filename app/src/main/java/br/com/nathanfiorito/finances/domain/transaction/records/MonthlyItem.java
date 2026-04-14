package br.com.nathanfiorito.finances.domain.transaction.records;

import java.math.BigDecimal;
import java.util.List;

public record MonthlyItem(int month, BigDecimal total, List<MonthlyCategoryItem> byCategory) {}
