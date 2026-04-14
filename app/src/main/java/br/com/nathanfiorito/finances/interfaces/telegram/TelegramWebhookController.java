package br.com.nathanfiorito.finances.interfaces.telegram;

import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.telegram.commands.CancelTransactionCommand;
import br.com.nathanfiorito.finances.application.telegram.commands.ChangeCategoryCommand;
import br.com.nathanfiorito.finances.application.telegram.commands.ConfirmTransactionCommand;
import br.com.nathanfiorito.finances.application.telegram.commands.ProcessMessageCommand;
import br.com.nathanfiorito.finances.application.telegram.usecases.CancelTransactionUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.ChangeCategoryUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.ConfirmTransactionUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.ProcessMessageUseCase;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort.NotificationButton;
import br.com.nathanfiorito.finances.infrastructure.telegram.config.TelegramProperties;
import br.com.nathanfiorito.finances.infrastructure.telegram.file.DownloadedFile;
import br.com.nathanfiorito.finances.infrastructure.telegram.file.TelegramFileDownloaderAdapter;
import br.com.nathanfiorito.finances.interfaces.telegram.dto.TelegramUpdateDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@RestController
@RequestMapping("/webhook")
@RequiredArgsConstructor
public class TelegramWebhookController {

    private final ProcessMessageUseCase processMessage;
    private final ConfirmTransactionUseCase confirmTransaction;
    private final CancelTransactionUseCase cancelTransaction;
    private final ChangeCategoryUseCase changeCategory;
    private final ListCategoriesUseCase listCategories;
    private final NotifierPort notifier;
    private final TelegramFileDownloaderAdapter fileDownloader;
    private final TelegramProperties telegramProperties;

    @PostMapping
    public ResponseEntity<Void> handleUpdate(@RequestBody TelegramUpdateDto update) {
        try {
            if (update.message() != null) {
                handleMessage(update.message());
            } else if (update.callbackQuery() != null) {
                handleCallback(update.callbackQuery());
            }
        } catch (Exception e) {
            log.error("Unhandled error processing Telegram update", e);
        }
        // Always return 200 so Telegram does not retry
        return ResponseEntity.ok().build();
    }

    // -------------------------------------------------------------------------
    // Message routing
    // -------------------------------------------------------------------------

    private void handleMessage(TelegramUpdateDto.MessageDto message) {
        long chatId = message.chat().id();
        if (chatId != telegramProperties.getAllowedChatId()) {
            log.warn("Ignoring message from unauthorized chat_id={}", chatId);
            return;
        }
        Long messageId = (long) message.messageId();

        if (message.text() != null) {
            processMessage.execute(new ProcessMessageCommand(chatId, "text", message.text(), messageId));

        } else if (message.photo() != null && !message.photo().isEmpty()) {
            String fileId = message.photo().get(message.photo().size() - 1).fileId();
            DownloadedFile file = fileDownloader.download(fileId, "image");
            processMessage.execute(new ProcessMessageCommand(chatId, file.entryType(), file.content(), messageId));

        } else if (message.document() != null
                && "application/pdf".equals(message.document().mimeType())) {
            DownloadedFile file = fileDownloader.download(message.document().fileId(), "pdf");
            processMessage.execute(new ProcessMessageCommand(chatId, file.entryType(), file.content(), messageId));

        } else {
            log.debug("Unsupported message type from chat_id={}", chatId);
        }
    }

    // -------------------------------------------------------------------------
    // Callback routing
    // -------------------------------------------------------------------------

    private void handleCallback(TelegramUpdateDto.CallbackQueryDto callback) {
        notifier.answerCallback(callback.id(), null);

        long chatId = callback.message().chat().id();
        long messageId = (long) callback.message().messageId();
        String data = callback.data();

        switch (data) {
            case "confirm" ->
                confirmTransaction.execute(new ConfirmTransactionCommand(chatId, messageId, false));
            case "force_confirm" ->
                confirmTransaction.execute(new ConfirmTransactionCommand(chatId, messageId, true));
            case "cancel" ->
                cancelTransaction.execute(new CancelTransactionCommand(chatId, messageId));
            case "edit_category" ->
                handleEditCategory(chatId, messageId);
            default -> {
                if (data != null && data.startsWith("set_category:")) {
                    handleSetCategory(chatId, messageId, data);
                } else {
                    log.debug("Unhandled callback data: {}", data);
                }
            }
        }
    }

    private void handleEditCategory(long chatId, long messageId) {
        List<Category> categories = listCategories
            .execute(new ListCategoriesQuery(0, 100, true))
            .items();
        List<List<NotificationButton>> buttons = buildCategoryButtons(categories);
        notifier.editMessage(chatId, messageId, "Escolha a categoria:", null, buttons);
    }

    private void handleSetCategory(long chatId, long messageId, String data) {
        // format: set_category:{id}:{name}
        String[] parts = data.split(":", 3);
        if (parts.length != 3) return;
        try {
            int categoryId = Integer.parseInt(parts[1]);
            String categoryName = parts[2];
            changeCategory.execute(new ChangeCategoryCommand(chatId, messageId, categoryName, categoryId));
        } catch (NumberFormatException e) {
            log.warn("Malformed set_category callback: {}", data);
        }
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private List<List<NotificationButton>> buildCategoryButtons(List<Category> categories) {
        List<List<NotificationButton>> rows = new ArrayList<>();
        List<NotificationButton> row = new ArrayList<>();
        for (Category cat : categories) {
            row.add(new NotificationButton(
                cat.name(), "set_category:" + cat.id() + ":" + cat.name()
            ));
            if (row.size() == 2) {
                rows.add(List.copyOf(row));
                row = new ArrayList<>();
            }
        }
        if (!row.isEmpty()) rows.add(List.copyOf(row));
        return rows;
    }
}
