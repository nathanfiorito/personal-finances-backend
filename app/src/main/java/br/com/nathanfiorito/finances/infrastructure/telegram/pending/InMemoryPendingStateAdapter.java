package br.com.nathanfiorito.finances.infrastructure.telegram.pending;

import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class InMemoryPendingStateAdapter implements PendingStatePort {

    private final ConcurrentHashMap<Long, PendingTransaction> store = new ConcurrentHashMap<>();

    @Override
    public void set(long chatId, PendingTransaction state) {
        log.debug("Pending state stored: chatId={}, pendingCount={}", chatId, store.size() + 1);
        store.put(chatId, state);
    }

    @Override
    public Optional<PendingTransaction> get(long chatId) {
        PendingTransaction state = store.get(chatId);
        if (state == null || state.isExpired()) {
            if (state != null) {
                log.debug("Pending state expired: chatId={}", chatId);
            }
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
        log.debug("Pending state category updated: chatId={}, category={}", chatId, category);
        store.put(chatId, new PendingTransaction(
            state.extracted(), category, categoryId,
            state.chatId(), state.messageId(), state.expiresAt()
        ));
        return true;
    }

    @Override
    public void clear(long chatId) {
        log.debug("Pending state cleared: chatId={}", chatId);
        store.remove(chatId);
    }
}
