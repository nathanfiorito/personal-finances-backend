package br.com.nathanfiorito.finances.interfaces.rest.category.dto;

import br.com.nathanfiorito.finances.domain.category.records.Category;

public record CategoryResponse(int id, String name, boolean isActive) {

    public static CategoryResponse from(Category category) {
        return new CategoryResponse(category.id(), category.name(), category.active());
    }
}
