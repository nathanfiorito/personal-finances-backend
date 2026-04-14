package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.commands.DeactivateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

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

        PageResult<Category> result = useCase.execute(new ListCategoriesQuery());

        assertThat(result.total()).isEqualTo(2);
        assertThat(result.items()).hasSize(2);
        assertThat(result.items()).allMatch(Category::active);
    }

    @Test
    void shouldReturnEmptyWhenNoActiveCategories() {
        Category created = createUseCase.execute(new CreateCategoryCommand("Alimentação"));
        new DeactivateCategoryUseCase(repository).execute(new DeactivateCategoryCommand(created.id()));

        PageResult<Category> result = useCase.execute(new ListCategoriesQuery());

        assertThat(result.total()).isZero();
        assertThat(result.items()).isEmpty();
    }

    @Test
    void shouldCapPageSizeAt100() {
        PageResult<Category> result = useCase.execute(new ListCategoriesQuery(0, 999, true));

        assertThat(result).isNotNull();
    }

    @Test
    void shouldIncludeInactiveCategoriesWhenActiveOnlyIsFalse() {
        Category created = createUseCase.execute(new CreateCategoryCommand("Alimentação"));
        new DeactivateCategoryUseCase(repository).execute(new DeactivateCategoryCommand(created.id()));

        PageResult<Category> result = useCase.execute(new ListCategoriesQuery(0, 20, false));

        assertThat(result.total()).isEqualTo(1);
    }
}
