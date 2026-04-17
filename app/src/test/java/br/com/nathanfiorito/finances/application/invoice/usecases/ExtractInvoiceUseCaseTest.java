package br.com.nathanfiorito.finances.application.invoice.usecases;

import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.ports.PdfTextExtractorPort;
import br.com.nathanfiorito.finances.domain.invoice.records.*;
import br.com.nathanfiorito.finances.domain.transaction.EstablishmentNormalizer;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.stubs.StubCardRepository;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import br.com.nathanfiorito.finances.stubs.StubInvoiceExtractorPort;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ExtractInvoiceUseCaseTest {

    private StubCardRepository cardRepo;
    private StubCategoryRepository categoryRepo;
    private StubTransactionRepository transactionRepo;
    private StubInvoiceExtractorPort llm;
    private final PdfTextExtractorPort pdf = bytes -> "INVOICE TEXT";
    private ExtractInvoiceUseCase useCase;

    @BeforeEach
    void setUp() {
        cardRepo = new StubCardRepository();
        categoryRepo = new StubCategoryRepository();
        transactionRepo = new StubTransactionRepository();
        llm = new StubInvoiceExtractorPort();
        useCase = new ExtractInvoiceUseCase(
            pdf, categoryRepo, cardRepo, llm, transactionRepo, new EstablishmentNormalizer());
    }

    @Test
    void matchesCardByLastFourDigits() {
        cardRepo.seed(new Card(2, "Itaú Black", "Itaú", "7981", 31, 7, true, null));
        llm.willReturn(new InvoiceExtractionRawResult("7981", List.of()));

        InvoiceImportPreview preview = useCase.execute(new byte[0], "fatura.pdf");

        assertThat(preview.detectedCard().matchedCardId()).isEqualTo(2);
        assertThat(preview.detectedCard().matchedCardAlias()).isEqualTo("Itaú Black");
        assertThat(preview.detectedCard().matchedCardBank()).isEqualTo("Itaú");
    }

    @Test
    void leavesCardUnmatchedWhenDigitsNotFound() {
        cardRepo.seed(new Card(2, "Itaú Black", "Itaú", "1111", 31, 7, true, null));
        llm.willReturn(new InvoiceExtractionRawResult("7981", List.of()));

        InvoiceImportPreview preview = useCase.execute(new byte[0], "fatura.pdf");

        assertThat(preview.detectedCard().lastFourDigits()).isEqualTo("7981");
        assertThat(preview.detectedCard().matchedCardId()).isNull();
    }

    @Test
    void flagsDuplicateWhenSameDateAmountAndSimilarEstablishment() {
        categoryRepo.seed(new Category(1, "Transporte", true));
        ExtractedTransaction existing = new ExtractedTransaction(
            new BigDecimal("35.99"), LocalDate.parse("2025-12-05"), "Uber UBER*TRIP",
            null, null, "invoice", TransactionType.EXPENSE, PaymentMethod.CREDIT, 1.0);
        transactionRepo.save(existing, 1, null);

        llm.willReturn(new InvoiceExtractionRawResult(null, List.of(
            new InvoiceExtractionRawResult.Item(
                LocalDate.parse("2025-12-05"), "UBER* TRIP", null,
                new BigDecimal("35.99"), 1, "Transporte", "transporte",
                false, null, null, 0.95))));

        InvoiceImportPreview preview = useCase.execute(new byte[0], "fatura.pdf");

        assertThat(preview.items()).hasSize(1);
        assertThat(preview.items().get(0).isPossibleDuplicate()).isTrue();
        assertThat(preview.items().get(0).duplicateOfTransactionId()).isNotNull();
    }

    @Test
    void assignsUniqueTempIds() {
        llm.willReturn(new InvoiceExtractionRawResult(null, List.of(
            item(LocalDate.parse("2025-12-05"), "A", new BigDecimal("1.00")),
            item(LocalDate.parse("2025-12-06"), "B", new BigDecimal("2.00")))));

        InvoiceImportPreview preview = useCase.execute(new byte[0], "fatura.pdf");
        assertThat(preview.items().get(0).tempId()).isNotBlank();
        assertThat(preview.items().get(0).tempId()).isNotEqualTo(preview.items().get(1).tempId());
    }

    @Test
    void propagatesLlmExceptionAsInvoiceImportException() {
        llm.willFailWith(new RuntimeException("llm down"));
        assertThatThrownBy(() -> useCase.execute(new byte[0], "fatura.pdf"))
            .isInstanceOf(InvoiceImportException.class);
    }

    private static InvoiceExtractionRawResult.Item item(LocalDate date, String est, BigDecimal amt) {
        return new InvoiceExtractionRawResult.Item(
            date, est, null, amt, null, null, null, false, null, null, 0.9);
    }
}
