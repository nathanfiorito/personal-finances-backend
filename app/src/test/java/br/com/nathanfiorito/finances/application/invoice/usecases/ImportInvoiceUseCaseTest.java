package br.com.nathanfiorito.finances.application.invoice.usecases;

import br.com.nathanfiorito.finances.application.invoice.commands.ImportInvoiceCommand;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.stubs.StubCardRepository;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ImportInvoiceUseCaseTest {

    private StubCardRepository cardRepo;
    private StubCategoryRepository categoryRepo;
    private StubTransactionRepository transactionRepo;
    private ImportInvoiceUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepo = new StubCardRepository();
        categoryRepo = new StubCategoryRepository();
        transactionRepo = new StubTransactionRepository();
        useCase = new ImportInvoiceUseCase(cardRepo, categoryRepo, transactionRepo);
    }

    @Test
    void importsAllItemsTaggingThemWithCardAndInvoiceEntryType() {
        cardRepo.seed(activeCard(2, "7981"));
        categoryRepo.seed(new Category(1, "Serviços", true));

        ImportInvoiceCommand cmd = new ImportInvoiceCommand(2, List.of(
            new ImportInvoiceCommand.Item(LocalDate.parse("2025-12-05"), "A", null, new BigDecimal("1.99"), 1),
            new ImportInvoiceCommand.Item(LocalDate.parse("2025-12-06"), "B", null, new BigDecimal("2.50"), 1)
        ));

        List<UUID> ids = useCase.execute(cmd);

        assertThat(ids).hasSize(2);
        List<Transaction> saved = transactionRepo.listByPeriod(
            LocalDate.parse("2025-12-01"), LocalDate.parse("2025-12-31"), Optional.empty());
        assertThat(saved).hasSize(2);
        assertThat(saved).allSatisfy(t -> {
            assertThat(t.entryType()).isEqualTo("invoice");
            assertThat(t.cardId()).isEqualTo(2);
        });
    }

    @Test
    void rejectsInactiveCard() {
        cardRepo.seed(inactiveCard(2, "7981"));
        categoryRepo.seed(new Category(1, "Serviços", true));

        ImportInvoiceCommand cmd = new ImportInvoiceCommand(2, List.of(
            new ImportInvoiceCommand.Item(LocalDate.parse("2025-12-05"), "A", null, new BigDecimal("1.99"), 1)));

        assertThatThrownBy(() -> useCase.execute(cmd))
            .isInstanceOf(InvoiceImportException.class)
            .hasMessageContaining("Card");
    }

    @Test
    void rejectsInactiveCategoryOnAnyRow() {
        cardRepo.seed(activeCard(2, "7981"));
        categoryRepo.seed(new Category(1, "Serviços", true));
        categoryRepo.seed(new Category(2, "Desativada", false));

        ImportInvoiceCommand cmd = new ImportInvoiceCommand(2, List.of(
            new ImportInvoiceCommand.Item(LocalDate.parse("2025-12-05"), "A", null, new BigDecimal("1.99"), 1),
            new ImportInvoiceCommand.Item(LocalDate.parse("2025-12-06"), "B", null, new BigDecimal("2.50"), 2)));

        assertThatThrownBy(() -> useCase.execute(cmd))
            .isInstanceOf(InvoiceImportException.class)
            .hasMessageContaining("category");
    }

    @Test
    void rejectsEmptyItems() {
        cardRepo.seed(activeCard(2, "7981"));

        assertThatThrownBy(() -> useCase.execute(new ImportInvoiceCommand(2, List.of())))
            .isInstanceOf(InvoiceImportException.class);
    }

    // --- helpers ---
    private static Card activeCard(int id, String lastFour) {
        return card(id, lastFour, true);
    }

    private static Card inactiveCard(int id, String lastFour) {
        return card(id, lastFour, false);
    }

    private static Card card(int id, String lastFour, boolean active) {
        // Card(int id, String alias, String bank, String lastFourDigits, int closingDay, int dueDay, boolean active, LocalDateTime createdAt)
        return new Card(id, "Itaú Black", "Itaú", lastFour, 31, 7, active, null);
    }
}
