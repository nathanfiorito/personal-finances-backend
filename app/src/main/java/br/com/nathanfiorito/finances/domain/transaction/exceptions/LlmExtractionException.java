package br.com.nathanfiorito.finances.domain.transaction.exceptions;

public class LlmExtractionException extends RuntimeException {
    public LlmExtractionException(String message) {
        super(message);
    }
    public LlmExtractionException(String message, Throwable cause) {
        super(message, cause);
    }
}
