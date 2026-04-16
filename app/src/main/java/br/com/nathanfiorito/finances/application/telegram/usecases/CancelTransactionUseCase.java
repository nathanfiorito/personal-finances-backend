package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.commands.CancelTransactionCommand;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class CancelTransactionUseCase {

    private final PendingStatePort pendingState;
    private final NotifierPort notifier;

    public void execute(CancelTransactionCommand cmd) {
        log.info("Transaction cancelled by user: chatId={}", cmd.chatId());
        pendingState.clear(cmd.chatId());
        notifier.editMessage(cmd.chatId(), cmd.messageId(), "❌ Transação cancelada.", null, null);
    }
}
