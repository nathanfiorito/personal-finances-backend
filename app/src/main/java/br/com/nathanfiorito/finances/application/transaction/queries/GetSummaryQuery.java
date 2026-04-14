package br.com.nathanfiorito.finances.application.transaction.queries;

import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;

import java.time.LocalDate;
import java.util.Optional;

public record GetSummaryQuery(LocalDate start, LocalDate end, Optional<TransactionType> type) {}
