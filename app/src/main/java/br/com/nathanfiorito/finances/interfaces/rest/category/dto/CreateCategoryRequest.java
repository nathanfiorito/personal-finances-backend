package br.com.nathanfiorito.finances.interfaces.rest.category.dto;

import jakarta.validation.constraints.NotBlank;

public record CreateCategoryRequest(
    @NotBlank(message = "Name is required") String name
) {}
