package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.UpdateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class UpdateCategoryUseCase {

    private final CategoryRepository repository;

    public Category execute(UpdateCategoryCommand command) {
        return repository.update(command.id(), command.name())
            .orElseThrow(() -> new CategoryNotFoundException(command.id()));
    }
}
