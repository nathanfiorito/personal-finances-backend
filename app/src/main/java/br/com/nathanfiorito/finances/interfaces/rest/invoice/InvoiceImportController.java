package br.com.nathanfiorito.finances.interfaces.rest.invoice;

import br.com.nathanfiorito.finances.application.invoice.commands.ImportInvoiceCommand;
import br.com.nathanfiorito.finances.application.invoice.usecases.ExtractInvoiceUseCase;
import br.com.nathanfiorito.finances.application.invoice.usecases.ImportInvoiceUseCase;
import br.com.nathanfiorito.finances.domain.invoice.exceptions.InvoiceImportException;
import br.com.nathanfiorito.finances.domain.invoice.records.DetectedCard;
import br.com.nathanfiorito.finances.domain.invoice.records.ExtractedInvoiceItem;
import br.com.nathanfiorito.finances.domain.invoice.records.InvoiceImportPreview;
import br.com.nathanfiorito.finances.interfaces.rest.invoice.dto.InvoiceImportPreviewResponse;
import br.com.nathanfiorito.finances.interfaces.rest.invoice.dto.InvoiceImportRequest;
import br.com.nathanfiorito.finances.interfaces.rest.invoice.dto.InvoiceImportResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("${app.api.base-path:/api/v1}/invoices/import")
@RequiredArgsConstructor
public class InvoiceImportController {

    private static final long MAX_UPLOAD_BYTES = 10L * 1024 * 1024;

    private final ExtractInvoiceUseCase extractUseCase;
    private final ImportInvoiceUseCase importUseCase;

    @PostMapping(path = "/preview", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<InvoiceImportPreviewResponse> preview(
            @RequestParam("file") MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new InvoiceImportException("file is required");
        }
        if (file.getSize() > MAX_UPLOAD_BYTES) {
            throw new InvoiceImportException("file exceeds 10 MB limit");
        }
        String contentType = file.getContentType();
        if (contentType == null || !contentType.toLowerCase().contains("pdf")) {
            throw new InvoiceImportException("file must be a PDF");
        }
        log.info("Invoice preview requested: filename={}, size={} bytes",
            file.getOriginalFilename(), file.getSize());
        InvoiceImportPreview preview = extractUseCase.execute(file.getBytes(), file.getOriginalFilename());
        return ResponseEntity.ok(toResponse(preview));
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<InvoiceImportResponse> importInvoice(
            @Valid @RequestBody InvoiceImportRequest request) {
        log.info("Invoice import requested: cardId={}, items={}",
            request.cardId(), request.items().size());
        ImportInvoiceCommand cmd = new ImportInvoiceCommand(
            request.cardId(),
            request.items().stream()
                .map(i -> new ImportInvoiceCommand.Item(
                    i.date(), i.establishment(), i.description(), i.amount(), i.categoryId()))
                .toList());
        List<UUID> ids = importUseCase.execute(cmd);
        return ResponseEntity.ok(new InvoiceImportResponse(ids.size(), request.cardId(), ids));
    }

    private InvoiceImportPreviewResponse toResponse(InvoiceImportPreview p) {
        DetectedCard dc = p.detectedCard();
        return new InvoiceImportPreviewResponse(
            p.sourceFileName(),
            new InvoiceImportPreviewResponse.DetectedCardDto(
                dc.lastFourDigits(), dc.matchedCardId(),
                dc.matchedCardAlias(), dc.matchedCardBank()),
            p.items().stream().map(this::toItem).toList());
    }

    private InvoiceImportPreviewResponse.Item toItem(ExtractedInvoiceItem i) {
        return new InvoiceImportPreviewResponse.Item(
            i.tempId(), i.date(), i.establishment(), i.description(), i.amount(),
            "EXPENSE", "CREDIT",
            i.suggestedCategoryId(), i.suggestedCategoryName(), i.issuerHint(),
            i.isInternational(), i.originalCurrency(), i.originalAmount(),
            i.isPossibleDuplicate(), i.duplicateOfTransactionId(), i.confidence());
    }
}
