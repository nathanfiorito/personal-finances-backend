package br.com.nathanfiorito.finances.interfaces.rest.invoice.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record InvoiceImportRequest(
    @NotNull Integer cardId,
    @NotEmpty @Valid List<Item> items
) {
    public record Item(
        @NotNull LocalDate date,
        @NotBlank @Size(max = 255) String establishment,
        @Size(max = 1024) String description,
        @NotNull @DecimalMin("0.01") BigDecimal amount,
        @NotNull Integer categoryId
    ) {}
}
