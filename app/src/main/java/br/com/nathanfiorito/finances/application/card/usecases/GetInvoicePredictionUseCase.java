package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator;
import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator.Period;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.ports.InvoicePredictionRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Slf4j
@RequiredArgsConstructor
public class GetInvoicePredictionUseCase {

    private final CardRepository cardRepository;
    private final TransactionRepository transactionRepository;
    private final InvoicePredictionRepository predictionRepository;
    private final LlmPort llmPort;

    public Optional<InvoicePrediction> execute(int cardId) {
        log.debug("Getting invoice prediction for card: id={}", cardId);

        Card card = cardRepository.findById(cardId)
            .orElseThrow(() -> {
                log.warn("Card not found: id={}", cardId);
                return new CardNotFoundException(cardId);
            });

        LocalDate today = LocalDate.now();
        Period currentPeriod = InvoicePeriodCalculator.currentPeriod(card.closingDay(), today);
        LocalDate invoiceMonth = currentPeriod.end();

        // Check cache: return if fresh (< 24h)
        Optional<InvoicePrediction> cached = predictionRepository.findByCardAndMonth(cardId, invoiceMonth);
        if (cached.isPresent() && cached.get().generatedAt() != null
                && cached.get().generatedAt().isAfter(LocalDateTime.now().minusHours(24))) {
            log.debug("Returning cached prediction for card {} month {}", cardId, invoiceMonth);
            return cached;
        }

        return generatePrediction(card, currentPeriod, today);
    }

    Optional<InvoicePrediction> generatePrediction(Card card, Period currentPeriod, LocalDate today) {
        // Collect historical totals from closed invoices
        List<BigDecimal> historicalTotals = collectHistoricalTotals(card, today, 6);

        if (historicalTotals.size() < 2) {
            log.debug("Not enough history for prediction: card={}, invoices={}", card.id(), historicalTotals.size());
            return Optional.empty();
        }

        List<Transaction> currentTransactions = transactionRepository.listByCardAndPeriod(
            card.id(), currentPeriod.start(), currentPeriod.end());

        BigDecimal currentTotal = currentTransactions.stream()
            .map(Transaction::amount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        int daysElapsed = (int) ChronoUnit.DAYS.between(currentPeriod.start(), today);
        int daysRemaining = (int) ChronoUnit.DAYS.between(today, currentPeriod.end());

        InvoicePrediction prediction = llmPort.generateInvoicePrediction(
            card.id(), currentTotal, currentTransactions.size(),
            daysElapsed, daysRemaining, historicalTotals);

        LocalDate invoiceMonth = currentPeriod.end();
        InvoicePrediction saved = predictionRepository.save(card.id(), invoiceMonth, prediction);
        log.debug("Generated prediction for card {} month {}: predicted={}",
            card.id(), invoiceMonth, saved.predictedTotal());

        return Optional.of(saved);
    }

    private List<BigDecimal> collectHistoricalTotals(Card card, LocalDate today, int maxMonths) {
        List<BigDecimal> totals = new ArrayList<>();
        Period period = InvoicePeriodCalculator.previousPeriod(card.closingDay(), today);

        for (int i = 0; i < maxMonths; i++) {
            List<Transaction> transactions = transactionRepository.listByCardAndPeriod(
                card.id(), period.start(), period.end());

            if (!transactions.isEmpty()) {
                BigDecimal total = transactions.stream()
                    .map(Transaction::amount)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
                totals.add(total);
            }

            // Move to the previous period
            LocalDate prevEnd = period.start().minusDays(1);
            LocalDate prevStart = InvoicePeriodCalculator.periodForMonth(
                card.closingDay(), prevEnd.getYear(), prevEnd.getMonthValue()).start();
            period = new Period(prevStart, prevEnd);
        }

        return totals;
    }
}
