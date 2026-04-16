package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.queries.GetInvoiceByMonthQuery;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.records.Invoice;
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

class GetInvoiceByMonthUseCaseTest {

    private StubCardRepository cardRepository;
    private StubTransactionRepository transactionRepository;
    private GetInvoiceByMonthUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepository = new StubCardRepository();
        transactionRepository = new StubTransactionRepository();
        useCase = new GetInvoiceByMonthUseCase(cardRepository, transactionRepository);
    }

    @Test
    void shouldThrowWhenCardNotFound() {
        assertThatThrownBy(() -> useCase.execute(new GetInvoiceByMonthQuery(999, 2026, 4)))
            .isInstanceOf(CardNotFoundException.class);
    }

    @Test
    void shouldReturnInvoiceForSpecificMonth() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        // Add a transaction within the March 2026 period (closing day 10 means period: Feb 11 - Mar 10)
        transactionRepository.save(
            new ExtractedTransaction(new BigDecimal("200.00"), LocalDate.of(2026, 3, 5),
                "Store B", "Purchase", null, "manual", TransactionType.EXPENSE,
                PaymentMethod.CREDIT, 1.0),
            1, card.id());

        Invoice invoice = useCase.execute(new GetInvoiceByMonthQuery(card.id(), 2026, 3));

        assertThat(invoice.cardId()).isEqualTo(card.id());
        assertThat(invoice.periodEnd()).isEqualTo(LocalDate.of(2026, 3, 10));
        assertThat(invoice.total()).isEqualByComparingTo("200.00");
        assertThat(invoice.transactions()).hasSize(1);
    }

    @Test
    void shouldReturnEmptyInvoiceWhenNoTransactionsInMonth() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        Invoice invoice = useCase.execute(new GetInvoiceByMonthQuery(card.id(), 2026, 1));

        assertThat(invoice.total()).isEqualByComparingTo("0");
        assertThat(invoice.transactions()).isEmpty();
    }
}
