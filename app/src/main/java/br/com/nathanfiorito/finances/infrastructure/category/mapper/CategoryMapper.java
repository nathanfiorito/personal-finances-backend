package br.com.nathanfiorito.finances.infrastructure.category.mapper;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;

public class CategoryMapper {

    private CategoryMapper() {}

    public static Category toDomain(CategoryEntity entity) {
        return new Category(entity.getId(), entity.getName(), entity.isActive());
    }
}
