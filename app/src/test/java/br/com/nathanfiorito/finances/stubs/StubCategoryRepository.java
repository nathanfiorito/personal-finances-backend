package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

public class StubCategoryRepository implements CategoryRepository {

    private final List<Category> categories = new ArrayList<>();
    private final AtomicInteger nextId = new AtomicInteger(1);

    @Override
    public Category save(String name) {
        Category category = new Category(nextId.getAndIncrement(), name, true);
        categories.add(category);
        return category;
    }

    @Override
    public Optional<Category> findById(int id) {
        return categories.stream().filter(c -> c.id() == id).findFirst();
    }

    @Override
    public List<Category> listActive() {
        return categories.stream().filter(Category::active).toList();
    }

    @Override
    public Optional<Category> update(int id, String name) {
        return categories.stream()
            .filter(c -> c.id() == id)
            .map(c -> new Category(c.id(), name, c.active()))
            .findFirst();
    }

    @Override
    public boolean deactivate(int id) {
        boolean found = categories.stream().anyMatch(c -> c.id() == id);
        if (found) {
            categories.replaceAll(c -> c.id() == id
                ? new Category(c.id(), c.name(), false)
                : c);
        }
        return found;
    }
}
