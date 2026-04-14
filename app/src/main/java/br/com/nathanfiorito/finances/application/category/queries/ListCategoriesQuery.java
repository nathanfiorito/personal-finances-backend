package br.com.nathanfiorito.finances.application.category.queries;

public record ListCategoriesQuery(boolean activeOnly) {
    public ListCategoriesQuery() {
        this(true);
    }
}
