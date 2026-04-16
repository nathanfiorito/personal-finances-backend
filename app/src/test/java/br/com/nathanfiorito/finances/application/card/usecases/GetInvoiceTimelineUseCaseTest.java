package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.queries.GetInvoiceTimelineQuery;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.records.InvoiceTimeline;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.stubs.StubCardRepository;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class GetInvoiceTimelineUseCaseTest {

    private StubCardRepository cardRepository;
    private StubTransactionRepository transactionRepository;
    private GetInvoiceTimelineUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepository = new StubCardRepository();
        transactionRepository = new StubTransactionRepository();
        useCase = new GetInvoiceTimelineUseCase(cardRepository, transactionRepository);
    }

    @Test
    void shouldThrowWhenCardNotFound() {
        assertThatThrownBy(() -> useCase.execute(new GetInvoiceTimelineQuery(999, 1)))
            .isInstanceOf(CardNotFoundException.class);
    }

    @Test
    void shouldReturnTimelineWithCurrentAndPrevious() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        // Add a transaction in the current period
        LocalDate today = LocalDate.now();
        transactionRepository.save(
            new ExtractedTransaction(new BigDecimal("50.00"), today, "Store A", "Purchase A",
                null, "manual", TransactionType.EXPENSE, PaymentMethod.CREDIT, 1.0),
            1, card.id());

        InvoiceTimeline timeline = useCase.execute(new GetInvoiceTimelineQuery(card.id(), 1));

        assertThat(timeline.current()).isNotNull();
        assertThat(timeline.previous()).isNotNull();
        assertThat(timeline.current().closingDate()).isNotNull();
        assertThat(timeline.current().dueDate()).isNotNull();
        assertThat(timeline.current().total()).isEqualByComparingTo("50.00");
        assertThat(timeline.current().daily()).isNotEmpty();
    }

    @Test
    void shouldCalculateDailyAccumulatedTotals() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        LocalDate today = LocalDate.now();
        LocalDate yesterday = today.minusDays(1);

        transactionRepository.save(
            new ExtractedTransaction(new BigDecimal("30.00"), yesterday, "Store A", "Purchase A",
                null, "manual", TransactionType.EXPENSE, PaymentMethod.CREDIT, 1.0),
            1, card.id());
        transactionRepository.save(
            new ExtractedTransaction(new BigDecimal("70.00"), today, "Store B", "Purchase B",
                null, "manual", TransactionType.EXPENSE, PaymentMethod.CREDIT, 1.0),
            1, card.id());

        InvoiceTimeline timeline = useCase.execute(new GetInvoiceTimelineQuery(card.id(), 1));

        assertThat(timeline.current().daily()).hasSize(2);
        assertThat(timeline.current().daily().get(0).accumulated()).isEqualByComparingTo("30.00");
        assertThat(timeline.current().daily().get(1).accumulated()).isEqualByComparingTo("100.00");
        assertThat(timeline.current().total()).isEqualByComparingTo("100.00");
    }

    @Test
    void shouldReturnEmptyTimelineWhenNoTransactions() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        InvoiceTimeline timeline = useCase.execute(new GetInvoiceTimelineQuery(card.id(), 1));

        assertThat(timeline.current().total()).isEqualByComparingTo("0");
        assertThat(timeline.current().daily()).isEmpty();
        assertThat(timeline.previous().total()).isEqualByComparingTo("0");
        assertThat(timeline.previous().daily()).isEmpty();
    }
}
