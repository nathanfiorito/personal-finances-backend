package br.com.nathanfiorito.finances.domain.category.exceptions;

public class CategoryNotFoundException extends RuntimeException {
    public CategoryNotFoundException(int id) {
        super("Category not found: " + id);
    }
}
