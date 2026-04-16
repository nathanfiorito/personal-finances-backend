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
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class RefreshInvoicePredictionUseCaseTest {

    private StubCardRepository cardRepository;
    private StubTransactionRepository transactionRepository;
    private StubInvoicePredictionRepository predictionRepository;
    private StubLlmPort llmPort;
    private RefreshInvoicePredictionUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepository = new StubCardRepository();
        transactionRepository = new StubTransactionRepository();
        predictionRepository = new StubInvoicePredictionRepository();
        llmPort = new StubLlmPort();
        useCase = new RefreshInvoicePredictionUseCase(cardRepository, transactionRepository, predictionRepository, llmPort);
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
    void shouldAlwaysRegenerateRegardlessOfCache() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);
        LocalDate today = LocalDate.now();

        // Seed historical transactions
        seedHistoricalTransactions(card.id(), card.closingDay(), today, 3);

        Optional<InvoicePrediction> first = useCase.execute(card.id());
        Optional<InvoicePrediction> second = useCase.execute(card.id());

        assertThat(first).isPresent();
        assertThat(second).isPresent();
        // Both should succeed (refresh always regenerates)
        assertThat(second.get().predictedTotal()).isNotNull();
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
