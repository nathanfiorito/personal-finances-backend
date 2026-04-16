package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.AmountFormatter;
import br.com.nathanfiorito.finances.application.telegram.commands.ConfirmTransactionCommand;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort.NotificationButton;
import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.Optional;

@Slf4j
@RequiredArgsConstructor
public class ConfirmTransactionUseCase {

    private final TransactionRepository transactionRepository;
    private final LlmPort llm;
    private final PendingStatePort pendingState;
    private final NotifierPort notifier;

    public void execute(ConfirmTransactionCommand cmd) {
        log.info("Confirming transaction: chatId={}, skipDuplicateCheck={}", cmd.chatId(), cmd.skipDuplicateCheck());
        Optional<PendingTransaction> stateOpt = pendingState.get(cmd.chatId());
        if (stateOpt.isEmpty()) {
            log.warn("Pending transaction expired or not found: chatId={}", cmd.chatId());
            notifier.editMessage(cmd.chatId(), cmd.messageId(),
                "⏱️ Operação expirada. Envie novamente.", null, null);
            return;
        }
        PendingTransaction state = stateOpt.get();

        if (!cmd.skipDuplicateCheck()) {
            notifier.editMessage(cmd.chatId(), cmd.messageId(),
                "⏳ Verificando duplicidades...", null, null);
            List<Transaction> recent = transactionRepository.listRecent(3);
            if (llm.isDuplicate(state.extracted(), recent)) {
                log.info("Duplicate detected: chatId={}, amount={}, establishment={}",
                    cmd.chatId(), state.extracted().amount(), state.extracted().establishment());
                List<List<NotificationButton>> buttons = List.of(List.of(
                    new NotificationButton("Salvar mesmo assim", "force_confirm"),
                    new NotificationButton("Cancelar ❌", "cancel")
                ));
                notifier.editMessage(cmd.chatId(), cmd.messageId(),
                    "⚠️ *Possível duplicidade detectada*\n\nDeseja salvar mesmo assim?",
                    "Markdown", buttons);
                return;
            }
            log.debug("No duplicate found: chatId={}", cmd.chatId());
        }

        notifier.editMessage(cmd.chatId(), cmd.messageId(),
            "⏳ Gravando no banco de dados...", null, null);
        try {
            Transaction saved = transactionRepository.save(state.extracted(), state.categoryId());
            pendingState.clear(cmd.chatId());
            log.info("Transaction confirmed and saved: id={}, chatId={}, amount={}, category={}",
                saved.id(), cmd.chatId(), saved.amount(), saved.category());
            notifier.sendMessage(cmd.chatId(),
                "✅ Transação de *" + AmountFormatter.format(saved.amount())
                    + "* em *" + saved.category() + "* registrada com sucesso!",
                "Markdown", null);
        } catch (Exception e) {
            log.error("Failed to save confirmed transaction: chatId={}", cmd.chatId(), e);
            notifier.sendMessage(cmd.chatId(),
                "❌ Erro ao salvar a transação. Tente novamente.", null, null);
        }
    }
}
