package br.com.nathanfiorito.finances.application.telegram.usecases;

import br.com.nathanfiorito.finances.application.telegram.commands.CancelTransactionCommand;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class CancelTransactionUseCase {

    private final PendingStatePort pendingState;
    private final NotifierPort notifier;

    public void execute(CancelTransactionCommand cmd) {
        pendingState.clear(cmd.chatId());
        notifier.editMessage(cmd.chatId(), cmd.messageId(), "❌ Transação cancelada.", null, null);
    }
}
