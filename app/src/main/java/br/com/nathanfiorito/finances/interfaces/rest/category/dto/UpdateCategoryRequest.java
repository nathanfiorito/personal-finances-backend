package br.com.nathanfiorito.finances.interfaces.rest.category.dto;

import jakarta.validation.constraints.NotBlank;

public record UpdateCategoryRequest(
    @NotBlank(message = "Name is required") String name
) {}
