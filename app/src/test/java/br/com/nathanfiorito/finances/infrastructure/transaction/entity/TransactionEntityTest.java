package br.com.nathanfiorito.finances.infrastructure.transaction.entity;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class TransactionEntityTest {

    @Test
    void onCreateShouldGenerateIdAndSetTimestamps() {
        TransactionEntity entity = new TransactionEntity();
        entity.onCreate();
        assertThat(entity.getId()).isNotNull();
        assertThat(entity.getCreatedAt()).isNotNull();
        assertThat(entity.getUpdatedAt()).isNotNull();
    }

    @Test
    void onUpdateShouldChangeUpdatedAtButNotCreatedAt() throws InterruptedException {
        TransactionEntity entity = new TransactionEntity();
        entity.onCreate();
        var originalCreatedAt = entity.getCreatedAt();
        var originalId = entity.getId();
        Thread.sleep(50);
        entity.onUpdate();
        assertThat(entity.getId()).isEqualTo(originalId);
        assertThat(entity.getCreatedAt()).isEqualTo(originalCreatedAt);
        assertThat(entity.getUpdatedAt()).isAfter(originalCreatedAt);
    }
}
