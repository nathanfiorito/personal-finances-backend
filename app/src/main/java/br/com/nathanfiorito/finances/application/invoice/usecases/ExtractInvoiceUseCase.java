package br.com.nathanfiorito.finances.application.invoice.usecases;

import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.ports.InvoiceExtractorPort;
import br.com.nathanfiorito.finances.domain.invoice.ports.PdfTextExtractorPort;
import br.com.nathanfiorito.finances.domain.invoice.records.DetectedCard;
import br.com.nathanfiorito.finances.domain.invoice.records.ExtractedInvoiceItem;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceExtractionRawResult;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceImportPreview;
import br.com.nathanfiorito.finances.domain.transaction.EstablishmentNormalizer;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public class ExtractInvoiceUseCase {

    private final PdfTextExtractorPort pdfExtractor;
    private final CategoryRepository categoryRepo;
    private final CardRepository cardRepo;
    private final InvoiceExtractorPort llm;
    private final TransactionRepository transactionRepo;
    private final EstablishmentNormalizer normalizer;

    public ExtractInvoiceUseCase(PdfTextExtractorPort pdfExtractor,
                                 CategoryRepository categoryRepo,
                                 CardRepository cardRepo,
                                 InvoiceExtractorPort llm,
                                 TransactionRepository transactionRepo,
                                 EstablishmentNormalizer normalizer) {
        this.pdfExtractor = pdfExtractor;
        this.categoryRepo = categoryRepo;
        this.cardRepo = cardRepo;
        this.llm = llm;
        this.transactionRepo = transactionRepo;
        this.normalizer = normalizer;
    }

    public InvoiceImportPreview execute(byte[] pdfBytes, String sourceFileName) {
        String text = pdfExtractor.extractText(pdfBytes);
        if (text == null || text.isBlank()) {
            throw new InvoiceImportException("PDF has no extractable text");
        }
        List<Category> categories = categoryRepo.listActive();
        List<Card> cards = cardRepo.listActive();

        InvoiceExtractionRawResult raw;
        try {
            raw = llm.extract(text, categories);
        } catch (InvoiceImportException e) {
            throw e;
        } catch (Exception e) {
            throw new InvoiceImportException("Invoice extraction failed: " + e.getMessage(), e);
        }

        DetectedCard detected = matchCard(raw.cardLastFourDigits(), cards);
        List<ExtractedInvoiceItem> items = raw.items().stream()
            .map(i -> enrich(i, categories))
            .toList();

        return new InvoiceImportPreview(sourceFileName, detected, items);
    }

    private DetectedCard matchCard(String lastFour, List<Card> cards) {
        if (lastFour == null) return DetectedCard.notDetected();
        List<Card> matches = cards.stream()
            .filter(c -> lastFour.equals(c.lastFourDigits()))
            .toList();
        if (matches.size() == 1) {
            Card c = matches.get(0);
            return new DetectedCard(lastFour, c.id(), c.alias(), c.bank());
        }
        return new DetectedCard(lastFour, null, null, null);
    }

    private ExtractedInvoiceItem enrich(InvoiceExtractionRawResult.Item i, List<Category> categories) {
        String categoryName = resolveCategoryName(i.suggestedCategoryId(), categories);
        DuplicateMatch dup = findDuplicate(i);
        return new ExtractedInvoiceItem(
            generateTempId(),
            i.date(),
            i.establishment(),
            i.description(),
            i.amount(),
            i.suggestedCategoryId(),
            categoryName,
            i.issuerHint(),
            i.isInternational(),
            i.originalCurrency(),
            i.originalAmount(),
            dup.isDuplicate,
            dup.existingId,
            i.confidence()
        );
    }

    private String resolveCategoryName(Integer id, List<Category> categories) {
        if (id == null) return null;
        return categories.stream()
            .filter(c -> Integer.valueOf(c.id()).equals(id))
            .map(Category::name)
            .findFirst()
            .orElse(null);
    }

    private DuplicateMatch findDuplicate(InvoiceExtractionRawResult.Item i) {
        List<Transaction> candidates = transactionRepo.listByPeriod(
            i.date(), i.date(), Optional.of(TransactionType.EXPENSE));
        BigDecimal tolerance = new BigDecimal("0.01");
        for (Transaction t : candidates) {
            if (t.amount().subtract(i.amount()).abs().compareTo(tolerance) <= 0
                && normalizer.areSameEstablishment(t.establishment(), i.establishment())) {
                return new DuplicateMatch(true, t.id());
            }
        }
        return new DuplicateMatch(false, null);
    }

    private String generateTempId() {
        return UUID.randomUUID().toString().substring(0, 8);
    }

    private record DuplicateMatch(boolean isDuplicate, UUID existingId) {}
}
