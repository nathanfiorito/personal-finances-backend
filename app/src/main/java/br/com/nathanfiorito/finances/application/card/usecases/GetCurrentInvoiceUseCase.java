package br.com.nathanfiorito.finances.application.card.usecases;

import br.com.nathanfiorito.finances.application.card.queries.GetCurrentInvoiceQuery;
import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator;
import br.com.nathanfiorito.finances.domain.card.InvoicePeriodCalculator.Period;
import br.com.nathanfiorito.finances.domain.card.exceptions.CardNotFoundException;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.card.records.Invoice;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Slf4j
@RequiredArgsConstructor
public class GetCurrentInvoiceUseCase {

    private final CardRepository cardRepository;
    private final TransactionRepository transactionRepository;

    public Invoice execute(GetCurrentInvoiceQuery query) {
        log.debug("Getting current invoice for card: id={}", query.cardId());

        Card card = cardRepository.findById(query.cardId())
            .orElseThrow(() -> {
                log.warn("Card not found: id={}", query.cardId());
                return new CardNotFoundException(query.cardId());
            });

        Period period = InvoicePeriodCalculator.currentPeriod(card.closingDay(), LocalDate.now());
        LocalDate dueDate = InvoicePeriodCalculator.dueDate(card.dueDay(), period.end());

        List<Transaction> transactions = transactionRepository.listByCardAndPeriod(
            card.id(), period.start(), period.end());

        BigDecimal total = transactions.stream()
            .map(Transaction::amount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        log.debug("Current invoice for card {}: period={} to {}, transactions={}, total={}",
            card.id(), period.start(), period.end(), transactions.size(), total);

        return new Invoice(card.id(), period.start(), period.end(), period.end(), dueDate, total, transactions);
    }
}
