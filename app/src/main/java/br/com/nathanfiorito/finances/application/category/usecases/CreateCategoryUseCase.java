package br.com.nathanfiorito.finances.application.category.usecases;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public class CreateCategoryUseCase {

    private final CategoryRepository repository;

    public Category execute(CreateCategoryCommand command) {
        log.info("Creating category: name={}", command.name());
        Category created = repository.save(command.name());
        log.info("Category created: id={}, name={}", created.id(), created.name());
        return created;
    }
}
