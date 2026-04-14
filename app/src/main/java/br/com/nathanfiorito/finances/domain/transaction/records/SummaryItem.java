package br.com.nathanfiorito.finances.domain.transaction.records;

import java.math.BigDecimal;

public record SummaryItem(String category, BigDecimal total, int count) {}
