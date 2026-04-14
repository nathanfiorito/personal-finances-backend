package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.stubs.StubCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class CreateCategoryUseCaseTest {

    private StubCategoryRepository repository;
    private CreateCategoryUseCase useCase;

    @BeforeEach
    void setUp() {
        repository = new StubCategoryRepository();
        useCase = new CreateCategoryUseCase(repository);
    }

    @Test
    void shouldCreateAndReturnCategory() {
        Category result = useCase.execute(new CreateCategoryCommand("Alimentação"));

        assertThat(result.name()).isEqualTo("Alimentação");
        assertThat(result.active()).isTrue();
        assertThat(result.id()).isGreaterThan(0);
    }

    @Test
    void shouldPersistCategoryInRepository() {
        useCase.execute(new CreateCategoryCommand("Transporte"));

        assertThat(repository.listPaginated(0, 20, true).total()).isEqualTo(1);
    }
}
