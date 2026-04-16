package br.com.nathanfiorito.finances.interfaces.rest.invoice.dto;

import br.com.nathanfiorito.finances.domain.card.records.InvoiceDailyEntry;
import br.com.nathanfiorito.finances.domain.card.records.InvoiceTimeline;
import br.com.nathanfiorito.finances.domain.card.records.InvoiceTimeline.InvoicePeriodSummary;

import java.util.List;

public record InvoiceTimelineResponse(
    PeriodSummaryResponse current,
    PeriodSummaryResponse previous
) {
    public static InvoiceTimelineResponse from(InvoiceTimeline timeline) {
        return new InvoiceTimelineResponse(
            PeriodSummaryResponse.from(timeline.current()),
            PeriodSummaryResponse.from(timeline.previous())
        );
    }

    public record PeriodSummaryResponse(
        String closingDate,
        String dueDate,
        String total,
        List<DailyEntryResponse> daily
    ) {
        public static PeriodSummaryResponse from(InvoicePeriodSummary summary) {
            List<DailyEntryResponse> entries = summary.daily().stream()
                .map(DailyEntryResponse::from)
                .toList();
            return new PeriodSummaryResponse(
                summary.closingDate().toString(),
                summary.dueDate().toString(),
                summary.total().toPlainString(),
                entries
            );
        }
    }

    public record DailyEntryResponse(
        String date,
        String amount,
        String accumulated
    ) {
        public static DailyEntryResponse from(InvoiceDailyEntry entry) {
            return new DailyEntryResponse(
                entry.date().toString(),
                entry.amount().toPlainString(),
                entry.accumulated().toPlainString()
            );
        }
    }
}
