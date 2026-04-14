package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public class StubPendingStatePort implements PendingStatePort {

    private final Map<Long, PendingTransaction> store = new HashMap<>();

    @Override
    public void set(long chatId, PendingTransaction state) {
        store.put(chatId, state);
    }

    @Override
    public Optional<PendingTransaction> get(long chatId) {
        PendingTransaction state = store.get(chatId);
        if (state == null || state.isExpired()) {
            store.remove(chatId);
            return Optional.empty();
        }
        return Optional.of(state);
    }

    @Override
    public boolean updateCategory(long chatId, String category, int categoryId) {
        PendingTransaction state = store.get(chatId);
        if (state == null || state.isExpired()) {
            store.remove(chatId);
            return false;
        }
        store.put(chatId, new PendingTransaction(
            state.extracted(), category, categoryId,
            state.chatId(), state.messageId(), state.expiresAt()
        ));
        return true;
    }

    @Override
    public void clear(long chatId) {
        store.remove(chatId);
    }

    public boolean hasState(long chatId) {
        return store.containsKey(chatId);
    }
}
