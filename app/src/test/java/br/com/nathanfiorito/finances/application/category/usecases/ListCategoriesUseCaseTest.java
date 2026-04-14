package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.commands.DeactivateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ListCategoriesUseCaseTest {

    private StubCategoryRepository repository;
    private ListCategoriesUseCase useCase;
    private CreateCategoryUseCase createUseCase;

    @BeforeEach
    void setUp() {
        repository = new StubCategoryRepository();
        useCase = new ListCategoriesUseCase(repository);
        createUseCase = new CreateCategoryUseCase(repository);
    }

    @Test
    void shouldReturnAllActiveCategories() {
        createUseCase.execute(new CreateCategoryCommand("Alimentação"));
        createUseCase.execute(new CreateCategoryCommand("Transporte"));

        List<Category> result = useCase.execute(new ListCategoriesQuery());

        assertThat(result).hasSize(2);
        assertThat(result).allMatch(Category::active);
    }

    @Test
    void shouldReturnEmptyWhenNoActiveCategories() {
        Category created = createUseCase.execute(new CreateCategoryCommand("Alimentação"));
        new DeactivateCategoryUseCase(repository).execute(new DeactivateCategoryCommand(created.id()));

        List<Category> result = useCase.execute(new ListCategoriesQuery());

        assertThat(result).isEmpty();
    }
}
