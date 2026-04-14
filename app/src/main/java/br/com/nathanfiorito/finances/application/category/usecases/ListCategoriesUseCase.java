package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import lombok.RequiredArgsConstructor;

import java.util.List;

@RequiredArgsConstructor
public class ListCategoriesUseCase {

    private final CategoryRepository repository;

    public List<Category> execute(ListCategoriesQuery query) {
        return repository.listActive();
    }
}
