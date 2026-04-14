package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.commands.UpdateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class UpdateCategoryUseCaseTest {

    private StubCategoryRepository repository;
    private UpdateCategoryUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubCategoryRepository();
        useCase = new UpdateCategoryUseCase(repository);
    }

    @Test
    void shouldReturnUpdatedCategory() {
        Category created = new CreateCategoryUseCase(repository)
            .execute(new CreateCategoryCommand("Alimentação"));

        Category result = useCase.execute(new UpdateCategoryCommand(created.id(), "Comida"));

        assertThat(result).isNotNull();
        assertThat(result.id()).isEqualTo(created.id());
    }

    @Test
    void shouldThrowWhenCategoryNotFound() {
        assertThatThrownBy(() ->
            useCase.execute(new UpdateCategoryCommand(999, "Nova"))
        ).isInstanceOf(CategoryNotFoundException.class);
    }
}
