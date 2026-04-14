package br.com.nathanfiorito.finances.application.transaction.queries;

import java.time.LocalDate;

public record ExportCsvQuery(LocalDate start, LocalDate end) {}
