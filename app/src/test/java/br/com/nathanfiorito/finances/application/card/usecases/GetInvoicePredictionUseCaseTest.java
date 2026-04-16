package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator;
import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator.Period;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.records.InvoicePrediction;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.stubs.StubCardRepository;
import br.com.nathanfiorito.finances.stubs.StubInvoicePredictionRepository;
import br.com.nathanfiorito.finances.stubs.StubLlmPort;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class GetInvoicePredictionUseCaseTest {

    private StubCardRepository cardRepository;
    private StubTransactionRepository transactionRepository;
    private StubInvoicePredictionRepository predictionRepository;
    private StubLlmPort llmPort;
    private GetInvoicePredictionUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepository = new StubCardRepository();
        transactionRepository = new StubTransactionRepository();
        predictionRepository = new StubInvoicePredictionRepository();
        llmPort = new StubLlmPort();
        useCase = new GetInvoicePredictionUseCase(cardRepository, transactionRepository, predictionRepository, llmPort);
    }

    @Test
    void shouldThrowWhenCardNotFound() {
        assertThatThrownBy(() -> useCase.execute(999))
            .isInstanceOf(CardNotFoundException.class);
    }

    @Test
    void shouldReturnEmptyWhenNotEnoughHistory() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        Optional<InvoicePrediction> result = useCase.execute(card.id());

        assertThat(result).isEmpty();
    }

    @Test
    void shouldReturnCachedPredictionWhenFresh() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);
        LocalDate today = LocalDate.now();
        Period currentPeriod = InvoicePeriodCalculator.currentPeriod(card.closingDay(), today);

        InvoicePrediction cached = new InvoicePrediction(
            card.id(), new BigDecimal("1500.00"), new BigDecimal("800.00"),
            10, new BigDecimal("50.00"), LocalDateTime.now().minusHours(1),
            "high", new BigDecimal("700.00"), 3);
        predictionRepository.save(card.id(), currentPeriod.end(), cached);

        Optional<InvoicePrediction> result = useCase.execute(card.id());

        assertThat(result).isPresent();
        assertThat(result.get().predictedTotal()).isEqualByComparingTo("1500.00");
    }

    @Test
    void shouldGenerateNewPredictionWhenEnoughHistory() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);
        LocalDate today = LocalDate.now();

        // Create enough historical transactions in previous periods
        seedHistoricalTransactions(card.id(), card.closingDay(), today, 3);

        Optional<InvoicePrediction> result = useCase.execute(card.id());

        assertThat(result).isPresent();
        assertThat(result.get().cardId()).isEqualTo(card.id());
        assertThat(result.get().predictedTotal()).isNotNull();
    }

    private void seedHistoricalTransactions(int cardId, int closingDay, LocalDate today, int months) {
        Period period = InvoicePeriodCalculator.previousPeriod(closingDay, today);

        for (int i = 0; i < months; i++) {
            LocalDate txDate = period.start().plusDays(1);
            transactionRepository.save(
                new ExtractedTransaction(new BigDecimal("500.00"), txDate, "Store " + i,
                    "Purchase", null, "manual", TransactionType.EXPENSE,
                    PaymentMethod.CREDIT, 1.0),
                1, cardId);

            // Move to the previous period
            LocalDate prevEnd = period.start().minusDays(1);
            Period prevPeriod = InvoicePeriodCalculator.periodForMonth(
                closingDay, prevEnd.getYear(), prevEnd.getMonthValue());
            period = new Period(prevPeriod.start(), prevEnd);
        }
    }
}
