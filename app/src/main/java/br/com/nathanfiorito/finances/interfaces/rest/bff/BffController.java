package br.com.nathanfiorito.finances.interfaces.rest.bff;

import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.transaction.queries.ListTransactionsQuery;
import br.com.nathanfiorito.finances.application.transaction.usecases.ListTransactionsUseCase;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.interfaces.rest.bff.dto.BffTransactionsResponse;
import br.com.nathanfiorito.finances.interfaces.rest.category.dto.CategoryResponse;
import br.com.nathanfiorito.finances.interfaces.rest.shared.PageResponse;
import br.com.nathanfiorito.finances.interfaces.rest.transaction.dto.TransactionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("${app.api.base-path}/bff")
@RequiredArgsConstructor
public class BffController {

    private final ListTransactionsUseCase listTransactions;
    private final ListCategoriesUseCase listCategories;

    @GetMapping("/transactions")
    public ResponseEntity<BffTransactionsResponse> getTransactions(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(name = "page_size", defaultValue = "20") int pageSize
    ) {
        PageResult<Transaction> txResult = listTransactions.execute(new ListTransactionsQuery(page, pageSize));
        PageResult<Category> catResult = listCategories.execute(new ListCategoriesQuery(0, 100, true));

        PageResponse<TransactionResponse> txPage = PageResponse.from(txResult, TransactionResponse::from, page, pageSize);
        List<CategoryResponse> categories = catResult.items().stream().map(CategoryResponse::from).toList();

        return ResponseEntity.ok(new BffTransactionsResponse(txPage, categories));
    }
}
