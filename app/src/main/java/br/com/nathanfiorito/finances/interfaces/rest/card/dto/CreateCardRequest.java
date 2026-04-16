package br.com.nathanfiorito.finances.interfaces.rest.card.dto;

import br.com.nathanfiorito.finances.application.card.commands.CreateCardCommand;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record CreateCardRequest(
    @NotBlank(message = "Alias is required") @Size(max = 100) String alias,
    @NotBlank(message = "Bank is required") @Size(max = 100) String bank,
    @NotBlank(message = "Last four digits is required") @Pattern(regexp = "\\d{4}", message = "Must be exactly 4 digits") String lastFourDigits,
    @NotNull(message = "Closing day is required") @Min(1) @Max(31) Integer closingDay,
    @NotNull(message = "Due day is required") @Min(1) @Max(31) Integer dueDay
) {
    public CreateCardCommand toCommand() {
        return new CreateCardCommand(alias, bank, lastFourDigits, closingDay, dueDay);
    }
}
