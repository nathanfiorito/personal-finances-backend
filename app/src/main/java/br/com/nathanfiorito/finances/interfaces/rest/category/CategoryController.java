package br.com.nathanfiorito.finances.interfaces.rest.category;

import br.com.nathanfiorito.finances.application.category.commands.CreateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.commands.DeactivateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.commands.UpdateCategoryCommand;
import br.com.nathanfiorito.finances.application.category.queries.ListCategoriesQuery;
import br.com.nathanfiorito.finances.application.category.usecases.CreateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.DeactivateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.UpdateCategoryUseCase;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.interfaces.rest.category.dto.CategoryResponse;
import br.com.nathanfiorito.finances.interfaces.rest.category.dto.CreateCategoryRequest;
import br.com.nathanfiorito.finances.interfaces.rest.category.dto.UpdateCategoryRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("${app.api.base-path}/categories")
@RequiredArgsConstructor
public class CategoryController {

    private final CreateCategoryUseCase createCategory;
    private final ListCategoriesUseCase listCategories;
    private final UpdateCategoryUseCase updateCategory;
    private final DeactivateCategoryUseCase deactivateCategory;

    @GetMapping
    public ResponseEntity<List<CategoryResponse>> list() {
        log.debug("GET /categories");
        List<CategoryResponse> categories = listCategories
            .execute(new ListCategoriesQuery(0, 100, false))
            .items()
            .stream()
            .map(CategoryResponse::from)
            .toList();
        log.debug("GET /categories: returned {} items", categories.size());
        return ResponseEntity.ok(categories);
    }

    @PostMapping
    public ResponseEntity<CategoryResponse> create(@RequestBody @Valid CreateCategoryRequest request) {
        log.info("POST /categories: name={}", request.name());
        Category category = createCategory.execute(new CreateCategoryCommand(request.name()));
        log.info("POST /categories: created id={}", category.id());
        return ResponseEntity.status(HttpStatus.CREATED).body(CategoryResponse.from(category));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<CategoryResponse> update(
        @PathVariable int id,
        @RequestBody @Valid UpdateCategoryRequest request
    ) {
        log.info("PATCH /categories/{}: name={}", id, request.name());
        Category category = updateCategory.execute(new UpdateCategoryCommand(id, request.name()));
        return ResponseEntity.ok(CategoryResponse.from(category));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deactivate(@PathVariable int id) {
        log.info("DELETE /categories/{}", id);
        deactivateCategory.execute(new DeactivateCategoryCommand(id));
        return ResponseEntity.noContent().build();
    }
}
