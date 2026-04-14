package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.DeactivateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class DeactivateCategoryUseCase {

    private final CategoryRepository repository;

    public void execute(DeactivateCategoryCommand command) {
        boolean deactivated = repository.deactivate(command.id());
        if (!deactivated) {
            throw new CategoryNotFoundException(command.id());
        }
    }
}
