package br.com.nathanfiorito.finances.interfaces.rest.bff.dto;

import br.com.nathanfiorito.finances.interfaces.rest.category.dto.CategoryResponse;
import br.com.nathanfiorito.finances.interfaces.rest.shared.PageResponse;
import br.com.nathanfiorito.finances.interfaces.rest.transaction.dto.TransactionResponse;

import java.util.List;

public record BffTransactionsResponse(
    PageResponse<TransactionResponse> transactions,
    List<CategoryResponse> categories
) {}
