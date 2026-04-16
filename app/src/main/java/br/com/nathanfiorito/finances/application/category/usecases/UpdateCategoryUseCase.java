package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.UpdateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class UpdateCategoryUseCase {

    private final CategoryRepository repository;

    public Category execute(UpdateCategoryCommand command) {
        log.info("Updating category: id={}, newName={}", command.id(), command.name());
        Category updated = repository.update(command.id(), command.name())
            .orElseThrow(() -> {
                log.warn("Category not found for update: id={}", command.id());
                return new CategoryNotFoundException(command.id());
            });
        log.info("Category updated: id={}, name={}", updated.id(), updated.name());
        return updated;
    }
}
