package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class ListCategoriesUseCase {

    private final CategoryRepository repository;

    public PageResult<Category> execute(ListCategoriesQuery query) {
        log.debug("Listing categories: page={}, pageSize={}, activeOnly={}", query.page(), query.pageSize(), query.activeOnly());
        PageResult<Category> result = repository.listPaginated(query.page(), query.pageSize(), query.activeOnly());
        log.debug("Listed categories: count={}, total={}", result.items().size(), result.total());
        return result;
    }
}
