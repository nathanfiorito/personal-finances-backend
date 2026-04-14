package br.com.nathanfiorito.finances.interfaces.rest.category;

import br.com.nathanfiorito.finances.application.category.usecases.CreateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.DeactivateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.UpdateCategoryUseCase;
import br.com.nathanfiorito.finances.domain.category.exceptions.CategoryNotFoundException;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(CategoryController.class)
class CategoryControllerIT extends BaseControllerIT {

    @MockitoBean private CreateCategoryUseCase createCategory;
    @MockitoBean private ListCategoriesUseCase listCategories;
    @MockitoBean private UpdateCategoryUseCase updateCategory;
    @MockitoBean private DeactivateCategoryUseCase deactivateCategory;

    private Category sampleCategory() {
        return new Category(1, "Alimentação", true);
    }

    @Test
    void listShouldReturnCategoriesWhenAuthenticated() throws Exception {
        when(listCategories.execute(any()))
            .thenReturn(new PageResult<>(List.of(sampleCategory()), 1));

        mockMvc.perform(get("/api/v1/categories")
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].name").value("Alimentação"))
            .andExpect(jsonPath("$[0].id").value(1));
    }

    @Test
    void listShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(get("/api/v1/categories"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void createShouldReturnCreatedCategoryWhenNameIsProvided() throws Exception {
        when(createCategory.execute(any())).thenReturn(sampleCategory());

        mockMvc.perform(post("/api/v1/categories")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"name": "Alimentação"}
                        """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("Alimentação"));
    }

    @Test
    void createShouldReturnBadRequestWhenNameIsMissing() throws Exception {
        mockMvc.perform(post("/api/v1/categories")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void updateShouldReturnUpdatedCategoryWhenFound() throws Exception {
        when(updateCategory.execute(any())).thenReturn(new Category(1, "Novo Nome", true));

        mockMvc.perform(patch("/api/v1/categories/1")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"name": "Novo Nome"}
                        """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Novo Nome"));
    }

    @Test
    void updateShouldReturnNotFoundWhenCategoryDoesNotExist() throws Exception {
        when(updateCategory.execute(any())).thenThrow(new CategoryNotFoundException(999));

        mockMvc.perform(patch("/api/v1/categories/999")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"name": "X"}
                        """))
            .andExpect(status().isNotFound());
    }

    @Test
    void deactivateShouldReturnNoContentWhenCategoryExists() throws Exception {
        mockMvc.perform(delete("/api/v1/categories/1")
                .header("Authorization", validToken()))
            .andExpect(status().isNoContent());
    }

    @Test
    void deactivateShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(delete("/api/v1/categories/1"))
            .andExpect(status().isUnauthorized());
    }
}
