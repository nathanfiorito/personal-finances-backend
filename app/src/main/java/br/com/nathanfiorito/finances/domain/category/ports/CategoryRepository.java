package br.com.nathanfiorito.finances.domain.category.ports;

import br.com.nathanfiorito.finances.domain.category.records.Category;

import br.com.nathanfiorito.finances.domain.shared.PageResult;

import java.util.Optional;

public interface CategoryRepository {
    Category save(String name);
    Optional<Category> findById(int id);
    PageResult<Category> listPaginated(int page, int pageSize, boolean activeOnly);
    Optional<Category> update(int id, String name);
    boolean deactivate(int id);
}
