package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.queries.GetCurrentInvoiceQuery;
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

class GetCurrentInvoiceUseCaseTest {

    private StubCardRepository cardRepository;
    private StubTransactionRepository transactionRepository;
    private GetCurrentInvoiceUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepository = new StubCardRepository();
        transactionRepository = new StubTransactionRepository();
        useCase = new GetCurrentInvoiceUseCase(cardRepository, transactionRepository);
    }

    @Test
    void shouldThrowWhenCardNotFound() {
        assertThatThrownBy(() -> useCase.execute(new GetCurrentInvoiceQuery(999)))
            .isInstanceOf(CardNotFoundException.class);
    }

    @Test
    void shouldReturnInvoiceWithTransactions() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        // Add a transaction within the current period
        LocalDate today = LocalDate.now();
        transactionRepository.save(
            new ExtractedTransaction(new BigDecimal("100.00"), today, "Store A", "Purchase",
                null, "manual", TransactionType.EXPENSE, PaymentMethod.CREDIT, 1.0),
            1, card.id());

        Invoice invoice = useCase.execute(new GetCurrentInvoiceQuery(card.id()));

        assertThat(invoice.cardId()).isEqualTo(card.id());
        assertThat(invoice.total()).isEqualByComparingTo("100.00");
        assertThat(invoice.transactions()).hasSize(1);
        assertThat(invoice.periodStart()).isNotNull();
        assertThat(invoice.periodEnd()).isNotNull();
        assertThat(invoice.dueDate()).isNotNull();
    }

    @Test
    void shouldReturnEmptyInvoiceWhenNoTransactions() {
        var card = cardRepository.save("Nubank", "Nubank", "1234", 10, 20);

        Invoice invoice = useCase.execute(new GetCurrentInvoiceQuery(card.id()));

        assertThat(invoice.cardId()).isEqualTo(card.id());
        assertThat(invoice.total()).isEqualByComparingTo("0");
        assertThat(invoice.transactions()).isEmpty();
    }
}
