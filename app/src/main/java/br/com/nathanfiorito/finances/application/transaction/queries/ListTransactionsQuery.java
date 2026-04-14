package br.com.nathanfiorito.finances.application.transaction.queries;

public record ListTransactionsQuery(int page, int pageSize) {

    public ListTransactionsQuery {
        if (page < 0) page = 0;
        if (pageSize < 1) pageSize = 1;
        if (pageSize > 100) pageSize = 100;
    }

    public ListTransactionsQuery() {
        this(0, 20);
    }
}
