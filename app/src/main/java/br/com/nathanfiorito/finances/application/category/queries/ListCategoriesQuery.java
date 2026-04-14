package br.com.nathanfiorito.finances.application.category.queries;

public record ListCategoriesQuery(int page, int pageSize, boolean activeOnly) {

    public ListCategoriesQuery {
        if (page < 0) page = 0;
        if (pageSize < 1) pageSize = 1;
        if (pageSize > 100) pageSize = 100;
    }

    public ListCategoriesQuery() {
        this(0, 20, true);
    }
}
