package br.com.nathanfiorito.finances.application.invoice.usecases;

import br.com.nathanfiorito.finances.application.invoice.commands.ImportInvoiceCommand;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.extern.slf4j.Slf4j;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Slf4j
public class ImportInvoiceUseCase {

    private final CardRepository cardRepo;
    private final CategoryRepository categoryRepo;
    private final TransactionRepository transactionRepo;

    public ImportInvoiceUseCase(CardRepository cardRepo,
                                CategoryRepository categoryRepo,
                                TransactionRepository transactionRepo) {
        this.cardRepo = cardRepo;
        this.categoryRepo = categoryRepo;
        this.transactionRepo = transactionRepo;
    }

    @Transactional
    public List<UUID> execute(ImportInvoiceCommand cmd) {
        if (cmd.items() == null || cmd.items().isEmpty()) {
            throw new InvoiceImportException("Items must not be empty");
        }
        log.info("Importing invoice: cardId={}, itemCount={}", cmd.cardId(), cmd.items().size());
        Card card = cardRepo.findById(cmd.cardId())
            .orElseThrow(() -> {
                log.warn("Card inactive or not found: cardId={}", cmd.cardId());
                return new InvoiceImportException("Card not found: " + cmd.cardId());
            });
        if (!card.active()) {
            log.warn("Card inactive or not found: cardId={}", cmd.cardId());
            throw new InvoiceImportException("Card " + cmd.cardId() + " is not active");
        }
        Set<Integer> activeCategoryIds = new HashSet<>();
        for (Category c : categoryRepo.listActive()) activeCategoryIds.add(c.id());
        for (ImportInvoiceCommand.Item i : cmd.items()) {
            if (!activeCategoryIds.contains(i.categoryId())) {
                log.warn("Invalid category in invoice import: categoryId={}", i.categoryId());
                throw new InvoiceImportException(
                    "Invalid or inactive category: " + i.categoryId());
            }
        }

        List<UUID> ids = new ArrayList<>();
        for (ImportInvoiceCommand.Item i : cmd.items()) {
            ExtractedTransaction e = new ExtractedTransaction(
                i.amount(), i.date(), i.establishment(), i.description(),
                null, "invoice", TransactionType.EXPENSE, PaymentMethod.CREDIT, 0.0);
            Transaction saved = transactionRepo.save(e, i.categoryId(), card.id());
            ids.add(saved.id());
        }
        log.info("Invoice import succeeded: cardId={}, savedCount={}", cmd.cardId(), ids.size());
        return ids;
    }
}
