package br.com.nathanfiorito.finances.domain.telegram.ports;

import br.com.nathanfiorito.finances.domain.telegram.records.PendingTransaction;

import java.util.Optional;

public interface PendingStatePort {

    void set(long chatId, PendingTransaction state);

    Optional<PendingTransaction> get(long chatId);

    /**
     * Updates the category on an existing pending state.
     *
     * @return false if the state is missing or expired
     */
    boolean updateCategory(long chatId, String category, int categoryId);

    void clear(long chatId);
}
