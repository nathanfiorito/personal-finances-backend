package br.com.nathanfiorito.finances.infrastructure.category.adapter;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.infrastructure.BaseRepositoryIT;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Import;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@Import(CategoryRepositoryAdapter.class)
class CategoryRepositoryAdapterIT extends BaseRepositoryIT {

    @Autowired
    private CategoryRepositoryAdapter adapter;

    @Test
    void saveShouldPersistCategoryWithGeneratedIdAndActiveFlagTrue() {
        Category category = adapter.save("Alimentação");

        assertThat(category.id()).isPositive();
        assertThat(category.name()).isEqualTo("Alimentação");
        assertThat(category.active()).isTrue();
    }

    @Test
    void listAllShouldReturnOnlyActiveCategories() {
        adapter.save("Ativa");
        Category deactivated = adapter.save("Inativa");
        adapter.deactivate(deactivated.id());

        List<Category> result = adapter.listAll();

        assertThat(result).extracting(Category::name).contains("Ativa");
        assertThat(result).extracting(Category::name).doesNotContain("Inativa");
    }

    @Test
    void findByIdShouldReturnCategoryWhenFound() {
        Category saved = adapter.save("Transport");

        Optional<Category> result = adapter.findById(saved.id());

        assertThat(result).isPresent();
        assertThat(result.get().name()).isEqualTo("Transport");
    }

    @Test
    void findByIdShouldReturnEmptyWhenNotFound() {
        Optional<Category> result = adapter.findById(Integer.MAX_VALUE);

        assertThat(result).isEmpty();
    }

    @Test
    void listPaginatedWithActiveOnlyShouldReturnOnlyActiveCategories() {
        adapter.save("ActiveA");
        Category toDeactivate = adapter.save("Inactive");
        adapter.save("ActiveB");
        adapter.deactivate(toDeactivate.id());

        PageResult<Category> result = adapter.listPaginated(0, 10, true);

        assertThat(result.items()).extracting(Category::name).containsExactlyInAnyOrder("ActiveA", "ActiveB");
        assertThat(result.total()).isEqualTo(2);
    }

    @Test
    void listPaginatedWithActiveOnlyFalseShouldReturnAllCategories() {
        adapter.save("Cat1");
        Category toDeactivate = adapter.save("Cat2");
        adapter.deactivate(toDeactivate.id());

        PageResult<Category> result = adapter.listPaginated(0, 10, false);

        assertThat(result.items()).extracting(Category::name).containsExactlyInAnyOrder("Cat1", "Cat2");
        assertThat(result.total()).isEqualTo(2);
    }

    @Test
    void listPaginatedShouldRespectPageSizeLimit() {
        for (int i = 1; i <= 5; i++) {
            adapter.save("Category" + i);
        }

        PageResult<Category> result = adapter.listPaginated(0, 2, false);

        assertThat(result.items()).hasSize(2);
        assertThat(result.total()).isEqualTo(5);
    }

    @Test
    void updateShouldChangeNameAndReturnUpdatedCategory() {
        Category saved = adapter.save("OldName");

        Optional<Category> result = adapter.update(saved.id(), "NewName");

        assertThat(result).isPresent();
        assertThat(result.get().name()).isEqualTo("NewName");
        assertThat(result.get().id()).isEqualTo(saved.id());
    }

    @Test
    void updateShouldReturnEmptyWhenCategoryNotFound() {
        Optional<Category> result = adapter.update(Integer.MAX_VALUE, "AnyName");

        assertThat(result).isEmpty();
    }

    @Test
    void deactivateShouldSetActiveFalseAndReturnTrue() {
        Category saved = adapter.save("ToDeactivate");

        boolean result = adapter.deactivate(saved.id());

        assertThat(result).isTrue();
        Optional<Category> found = adapter.findById(saved.id());
        assertThat(found).isPresent();
        assertThat(found.get().active()).isFalse();
    }

    @Test
    void deactivateShouldReturnFalseWhenCategoryNotFound() {
        boolean result = adapter.deactivate(Integer.MAX_VALUE);

        assertThat(result).isFalse();
    }
}
