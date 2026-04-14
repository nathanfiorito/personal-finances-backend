package br.com.nathanfiorito.finances.infrastructure.category.mapper;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class CategoryMapperTest {

    @Test
    void toDomainShouldMapAllFields() {
        CategoryEntity entity = new CategoryEntity();
        entity.setId(1);
        entity.setName("Food");
        entity.setActive(true);

        Category result = CategoryMapper.toDomain(entity);

        assertThat(result.id()).isEqualTo(1);
        assertThat(result.name()).isEqualTo("Food");
        assertThat(result.active()).isTrue();
    }

    @Test
    void toDomainShouldMapInactiveCategory() {
        CategoryEntity entity = new CategoryEntity();
        entity.setId(2);
        entity.setName("Archived");
        entity.setActive(false);

        Category result = CategoryMapper.toDomain(entity);

        assertThat(result.active()).isFalse();
    }
}
