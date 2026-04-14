package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.commands.DeactivateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DeactivateCategoryUseCaseTest {

    private StubCategoryRepository repository;
    private DeactivateCategoryUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubCategoryRepository();
        useCase = new DeactivateCategoryUseCase(repository);
    }

    @Test
    void shouldDeactivateExistingCategory() {
        Category created = new CreateCategoryUseCase(repository)
            .execute(new CreateCategoryCommand("Alimentação"));

        assertThatCode(() ->
            useCase.execute(new DeactivateCategoryCommand(created.id()))
        ).doesNotThrowAnyException();
    }

    @Test
    void shouldThrowWhenCategoryNotFound() {
        assertThatThrownBy(() ->
            useCase.execute(new DeactivateCategoryCommand(999))
        ).isInstanceOf(CategoryNotFoundException.class);
    }
}
