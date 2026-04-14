package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class ListCategoriesUseCase {

    private final CategoryRepository repository;

    public PageResult<Category> execute(ListCategoriesQuery query) {
        return repository.listPaginated(query.page(), query.pageSize(), query.activeOnly());
    }
}
