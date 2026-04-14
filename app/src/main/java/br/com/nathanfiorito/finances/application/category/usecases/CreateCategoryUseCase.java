package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class CreateCategoryUseCase {

    private final CategoryRepository repository;

    public Category execute(CreateCategoryCommand command) {
        return repository.save(command.name());
    }
}
