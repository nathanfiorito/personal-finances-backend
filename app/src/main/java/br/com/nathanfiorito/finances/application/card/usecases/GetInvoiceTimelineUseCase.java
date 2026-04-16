package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.queries.GetInvoiceTimelineQuery;
import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator;
import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator.Period;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.card.records.InvoiceDailyEntry;
import br.com.nathanfiorito.finances.domain.card.records.InvoiceTimeline;
import br.com.nathanfiorito.finances.domain.card.records.InvoiceTimeline.InvoicePeriodSummary;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;

@Slf4j
@RequiredArgsConstructor
public class GetInvoiceTimelineUseCase {

    private final CardRepository cardRepository;
    private final TransactionRepository transactionRepository;

    public InvoiceTimeline execute(GetInvoiceTimelineQuery query) {
        log.debug("Getting invoice timeline for card: id={}, months={}", query.cardId(), query.months());

        Card card = cardRepository.findById(query.cardId())
            .orElseThrow(() -> {
                log.warn("Card not found: id={}", query.cardId());
                return new CardNotFoundException(query.cardId());
            });

        LocalDate today = LocalDate.now();
        Period currentPeriod = InvoicePeriodCalculator.currentPeriod(card.closingDay(), today);
        Period previousPeriod = InvoicePeriodCalculator.previousPeriod(card.closingDay(), today);

        InvoicePeriodSummary currentSummary = buildSummary(card, currentPeriod);
        InvoicePeriodSummary previousSummary = buildSummary(card, previousPeriod);

        log.debug("Timeline for card {}: current total={}, previous total={}",
            card.id(), currentSummary.total(), previousSummary.total());

        return new InvoiceTimeline(currentSummary, previousSummary);
    }

    private InvoicePeriodSummary buildSummary(Card card, Period period) {
        LocalDate dueDate = InvoicePeriodCalculator.dueDate(card.dueDay(), period.end());
        List<Transaction> transactions = transactionRepository.listByCardAndPeriod(
            card.id(), period.start(), period.end());

        BigDecimal total = transactions.stream()
            .map(Transaction::amount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        // Group transactions by date and calculate daily accumulated totals
        TreeMap<LocalDate, BigDecimal> dailyTotals = new TreeMap<>();
        for (Transaction tx : transactions) {
            dailyTotals.merge(tx.date(), tx.amount(), BigDecimal::add);
        }

        List<InvoiceDailyEntry> daily = new ArrayList<>();
        BigDecimal accumulated = BigDecimal.ZERO;
        for (var entry : dailyTotals.entrySet()) {
            accumulated = accumulated.add(entry.getValue());
            daily.add(new InvoiceDailyEntry(entry.getKey(), entry.getValue(), accumulated));
        }

        return new InvoicePeriodSummary(period.end(), dueDate, total, daily);
    }
}
