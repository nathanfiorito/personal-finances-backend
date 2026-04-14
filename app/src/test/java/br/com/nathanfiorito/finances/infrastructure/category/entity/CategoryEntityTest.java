package br.com.nathanfiorito.finances.infrastructure.category.entity;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class CategoryEntityTest {

    @Test
    void onCreateShouldSetBothTimestamps() {
        CategoryEntity entity = new CategoryEntity();
        entity.onCreate();
        assertThat(entity.getCreatedAt()).isNotNull();
        assertThat(entity.getUpdatedAt()).isNotNull();
    }

    @Test
    void onUpdateShouldChangeUpdatedAtButNotCreatedAt() throws InterruptedException {
        CategoryEntity entity = new CategoryEntity();
        entity.onCreate();
        var originalCreatedAt = entity.getCreatedAt();
        Thread.sleep(50);
        entity.onUpdate();
        assertThat(entity.getCreatedAt()).isEqualTo(originalCreatedAt);
        assertThat(entity.getUpdatedAt()).isAfter(originalCreatedAt);
    }
}
