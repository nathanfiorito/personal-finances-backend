package br.com.nathanfiorito.finances.domain.transaction.records;

import java.math.BigDecimal;

public record MonthlyCategoryItem(String category, BigDecimal total) {}
