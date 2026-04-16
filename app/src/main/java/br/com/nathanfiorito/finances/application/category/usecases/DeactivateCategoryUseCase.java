package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.DeactivateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class DeactivateCategoryUseCase {

    private final CategoryRepository repository;

    public void execute(DeactivateCategoryCommand command) {
        log.info("Deactivating category: id={}", command.id());
        boolean deactivated = repository.deactivate(command.id());
        if (!deactivated) {
            log.warn("Category not found for deactivation: id={}", command.id());
            throw new CategoryNotFoundException(command.id());
        }
        log.info("Category deactivated: id={}", command.id());
    }
}
