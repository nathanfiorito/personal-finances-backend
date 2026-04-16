package br.com.nathanfiorito.finances.interfaces.rest.shared;

import org.springframework.http.HttpStatus;

import java.time.LocalDateTime;
import java.util.Map;

public record ErrorResponse(
    int status,
    String error,
    String message,
    LocalDateTime timestamp,
    Map<String, String> details
) {

    public static ErrorResponse of(HttpStatus httpStatus, String message) {
        return new ErrorResponse(
            httpStatus.value(),
            httpStatus.getReasonPhrase(),
            message,
            LocalDateTime.now(),
            null
        );
    }

    public static ErrorResponse of(HttpStatus httpStatus, String message, Map<String, String> details) {
        return new ErrorResponse(
            httpStatus.value(),
            httpStatus.getReasonPhrase(),
            message,
            LocalDateTime.now(),
            details
        );
    }
}
