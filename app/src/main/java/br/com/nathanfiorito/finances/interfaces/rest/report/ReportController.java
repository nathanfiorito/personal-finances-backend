package br.com.nathanfiorito.finances.interfaces.rest.report;

import br.com.nathanfiorito.finances.application.transaction.queries.ExportCsvQuery;
import br.com.nathanfiorito.finances.application.transaction.queries.GetMonthlyQuery;
import br.com.nathanfiorito.finances.application.transaction.queries.GetSummaryQuery;
import br.com.nathanfiorito.finances.application.transaction.usecases.ExportCsvUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetMonthlyUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetSummaryUseCase;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.interfaces.rest.report.dto.MonthlyItemResponse;
import br.com.nathanfiorito.finances.interfaces.rest.report.dto.SummaryItemResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("${app.api.base-path}")
@RequiredArgsConstructor
public class ReportController {

    private final GetSummaryUseCase getSummary;
    private final GetMonthlyUseCase getMonthly;
    private final ExportCsvUseCase exportCsv;

    @GetMapping("/reports/summary")
    public ResponseEntity<List<SummaryItemResponse>> summary(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
        @RequestParam(required = false) TransactionType type
    ) {
        List<SummaryItemResponse> items = getSummary
            .execute(new GetSummaryQuery(start, end, Optional.ofNullable(type)))
            .stream()
            .map(SummaryItemResponse::from)
            .toList();
        return ResponseEntity.ok(items);
    }

    @GetMapping("/reports/monthly")
    public ResponseEntity<List<MonthlyItemResponse>> monthly(
        @RequestParam int year
    ) {
        List<MonthlyItemResponse> items = getMonthly
            .execute(new GetMonthlyQuery(year))
            .stream()
            .map(MonthlyItemResponse::from)
            .toList();
        return ResponseEntity.ok(items);
    }

    @GetMapping("/export/csv")
    public ResponseEntity<byte[]> exportCsv(
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end
    ) {
        byte[] content = exportCsv.execute(new ExportCsvQuery(start, end));
        String filename = "transactions_" + start + "_" + end + ".csv";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType("text/csv;charset=UTF-8"));
        headers.setContentDisposition(ContentDisposition.attachment().filename(filename).build());

        return ResponseEntity.ok().headers(headers).body(content);
    }
}
