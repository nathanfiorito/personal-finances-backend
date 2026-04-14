package br.com.nathanfiorito.finances.domain.category.ports;

import br.com.nathanfiorito.finances.domain.category.records.Category;

import java.util.List;
import java.util.Optional;

public interface CategoryRepository {
    Category save(String name);
    Optional<Category> findById(int id);
    List<Category> listActive();
    Optional<Category> update(int id, String name);
    boolean deactivate(int id);
}
