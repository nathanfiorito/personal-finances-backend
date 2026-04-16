package br.com.nathanfiorito.finances.domain.invoice.exceptions;

public class InvoiceImportException extends RuntimeException {
    public InvoiceImportException(String message) {
        super(message);
    }
    public InvoiceImportException(String message, Throwable cause) {
        super(message, cause);
    }
}
