package br.com.nathanfiorito.finances.domain.transaction.exceptions;

import java.util.UUID;

public class TransactionNotFoundException extends RuntimeException {
    public TransactionNotFoundException(UUID id) {
        super("Transaction not found: " + id);
    }
}
