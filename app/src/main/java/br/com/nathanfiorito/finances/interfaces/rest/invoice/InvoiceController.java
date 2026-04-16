package br.com.nathanfiorito.finances.interfaces.rest.invoice;

import br.com.nathanfiorito.finances.application.card.queries.GetCurrentInvoiceQuery;
import br.com.nathanfiorito.finances.application.card.queries.GetInvoiceByMonthQuery;
import br.com.nathanfiorito.finances.application.card.queries.GetInvoiceTimelineQuery;
import br.com.nathanfiorito.finances.application.card.usecases.GetCurrentInvoiceUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.GetInvoiceByMonthUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.GetInvoicePredictionUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.GetInvoiceTimelineUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.RefreshInvoicePredictionUseCase;
import br.com.nathanfiorito.finances.interfaces.rest.invoice.dto.InvoicePredictionResponse;
import br.com.nathanfiorito.finances.interfaces.rest.invoice.dto.InvoiceResponse;
import br.com.nathanfiorito.finances.interfaces.rest.invoice.dto.InvoiceTimelineResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("${app.api.base-path}/cards/{cardId}/invoices")
@RequiredArgsConstructor
public class InvoiceController {

    private final GetCurrentInvoiceUseCase getCurrentInvoice;
    private final GetInvoiceByMonthUseCase getInvoiceByMonth;
    private final GetInvoiceTimelineUseCase getInvoiceTimeline;
    private final GetInvoicePredictionUseCase getInvoicePrediction;
    private final RefreshInvoicePredictionUseCase refreshInvoicePrediction;

    @GetMapping("/current")
    public ResponseEntity<InvoiceResponse> getCurrent(@PathVariable int cardId) {
        log.debug("GET /cards/{}/invoices/current", cardId);
        var invoice = getCurrentInvoice.execute(new GetCurrentInvoiceQuery(cardId));
        return ResponseEntity.ok(InvoiceResponse.from(invoice));
    }

    @GetMapping("/{year}/{month}")
    public ResponseEntity<InvoiceResponse> getByMonth(
        @PathVariable int cardId,
        @PathVariable int year,
        @PathVariable int month
    ) {
        log.debug("GET /cards/{}/invoices/{}/{}", cardId, year, month);
        var invoice = getInvoiceByMonth.execute(new GetInvoiceByMonthQuery(cardId, year, month));
        return ResponseEntity.ok(InvoiceResponse.from(invoice));
    }

    @GetMapping("/timeline")
    public ResponseEntity<InvoiceTimelineResponse> getTimeline(
        @PathVariable int cardId,
        @RequestParam(defaultValue = "1") int months
    ) {
        log.debug("GET /cards/{}/invoices/timeline?months={}", cardId, months);
        var timeline = getInvoiceTimeline.execute(new GetInvoiceTimelineQuery(cardId, months));
        return ResponseEntity.ok(InvoiceTimelineResponse.from(timeline));
    }

    @GetMapping("/prediction")
    public ResponseEntity<InvoicePredictionResponse> getPrediction(@PathVariable int cardId) {
        log.debug("GET /cards/{}/invoices/prediction", cardId);
        return getInvoicePrediction.execute(cardId)
            .map(p -> ResponseEntity.ok(InvoicePredictionResponse.from(p)))
            .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @PostMapping("/prediction/refresh")
    public ResponseEntity<InvoicePredictionResponse> refreshPrediction(@PathVariable int cardId) {
        log.info("POST /cards/{}/invoices/prediction/refresh", cardId);
        return refreshInvoicePrediction.execute(cardId)
            .map(p -> ResponseEntity.ok(InvoicePredictionResponse.from(p)))
            .orElseGet(() -> ResponseEntity.noContent().build());
    }
}
