package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.AmountFormatter;
import br.com.nathanfiorito.finances.application.telegram.commands.ProcessMessageCommand;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort.NotificationButton;
import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import lombok.RequiredArgsConstructor;

import java.time.format.DateTimeFormatter;
import java.util.List;

@RequiredArgsConstructor
public class ProcessMessageUseCase {

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("dd/MM/yyyy");

    private final LlmPort llm;
    private final CategoryRepository categoryRepository;
    private final PendingStatePort pendingState;
    private final NotifierPort notifier;

    public void execute(ProcessMessageCommand cmd) {
        ExtractedTransaction extracted = llm.extractTransaction(cmd.content(), cmd.entryType());

        List<Category> categories = categoryRepository.listAll();
        List<String> categoryNames = categories.stream().map(Category::name).toList();
        String categoryName = llm.categorize(extracted, categoryNames);
        int categoryId = categories.stream()
            .filter(c -> c.name().equals(categoryName))
            .findFirst()
            .map(Category::id)
            .orElseGet(() -> categories.isEmpty() ? 1 : categories.get(0).id());

        PendingTransaction state = PendingTransaction.create(
            extracted, categoryName, categoryId, cmd.chatId(), cmd.messageId()
        );
        pendingState.set(cmd.chatId(), state);

        notifier.sendMessage(
            cmd.chatId(),
            buildConfirmationMessage(extracted, categoryName),
            "Markdown",
            buildConfirmationButtons()
        );
    }

    private String buildConfirmationMessage(ExtractedTransaction extracted, String category) {
        String dateStr = extracted.date() != null
            ? extracted.date().format(DATE_FMT)
            : "data não encontrada";
        String typeLabel = extracted.transactionType() == TransactionType.INCOME
            ? "Receita 💚" : "Despesa 🔴";

        StringBuilder sb = new StringBuilder();
        sb.append("*")
            .append(extracted.establishment() != null ? extracted.establishment() : "Estabelecimento desconhecido")
            .append("*\n");
        sb.append("Tipo: ").append(typeLabel).append("\n");
        sb.append("Valor: ").append(AmountFormatter.format(extracted.amount())).append("\n");
        sb.append("Data: ").append(dateStr).append("\n");
        sb.append("Categoria: ").append(category);
        if (extracted.description() != null) {
            sb.append("\nDescrição: ").append(extracted.description());
        }
        return sb.toString();
    }

    private List<List<NotificationButton>> buildConfirmationButtons() {
        return List.of(
            List.of(
                new NotificationButton("Confirmar ✅", "confirm"),
                new NotificationButton("Cancelar ❌", "cancel")
            ),
            List.of(
                new NotificationButton("Alterar Categoria 🏷️", "edit_category")
            )
        );
    }
}
