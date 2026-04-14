package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.AmountFormatter;
import br.com.nathanfiorito.finances.application.telegram.commands.ChangeCategoryCommand;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort.NotificationButton;
import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import lombok.RequiredArgsConstructor;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;

@RequiredArgsConstructor
public class ChangeCategoryUseCase {

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("dd/MM/yyyy");

    private final PendingStatePort pendingState;
    private final NotifierPort notifier;

    public void execute(ChangeCategoryCommand cmd) {
        boolean updated = pendingState.updateCategory(
            cmd.chatId(), cmd.newCategory(), cmd.newCategoryId()
        );
        if (!updated) {
            notifier.editMessage(cmd.chatId(), cmd.messageId(),
                "⏱️ Operação expirada. Envie a transação novamente.", null, null);
            return;
        }
        Optional<PendingTransaction> stateOpt = pendingState.get(cmd.chatId());
        if (stateOpt.isEmpty()) return;

        PendingTransaction state = stateOpt.get();
        notifier.editMessage(
            cmd.chatId(),
            cmd.messageId(),
            buildMessage(state.extracted(), cmd.newCategory()),
            "Markdown",
            buildConfirmationButtons()
        );
    }

    private String buildMessage(ExtractedTransaction extracted, String category) {
        String dateStr = extracted.date() != null
            ? extracted.date().format(DATE_FMT)
            : "data não encontrada";

        StringBuilder sb = new StringBuilder();
        sb.append("*")
            .append(extracted.establishment() != null ? extracted.establishment() : "Estabelecimento desconhecido")
            .append("*\n");
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
