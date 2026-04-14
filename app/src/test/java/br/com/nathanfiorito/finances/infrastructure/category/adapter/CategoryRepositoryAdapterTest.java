package br.com.nathanfiorito.finances.infrastructure.category.adapter;

import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.category.repository.JpaCategoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

class CategoryRepositoryAdapterTest {

    private StubJpaCategoryRepository jpa;
    private CategoryRepositoryAdapter adapter;

    @BeforeEach
    void setUp() {
        jpa = new StubJpaCategoryRepository();
        adapter = new CategoryRepositoryAdapter(jpa);
    }

    @Test
    void saveShouldPersistAndReturnDomainCategory() {
        Category result = adapter.save("Food");

        assertThat(result.id()).isEqualTo(1);
        assertThat(result.name()).isEqualTo("Food");
        assertThat(result.active()).isTrue();
        assertThat(jpa.lastSavedEntity).isNotNull();
        assertThat(jpa.lastSavedEntity.getName()).isEqualTo("Food");
    }

    @Test
    void findByIdShouldReturnMappedCategoryWhenFound() {
        CategoryEntity entity = new CategoryEntity();
        entity.setId(1);
        entity.setName("Food");
        entity.setActive(true);
        jpa.store(1, entity);

        Optional<Category> result = adapter.findById(1);

        assertThat(result).isPresent();
        assertThat(result.get().name()).isEqualTo("Food");
    }

    @Test
    void findByIdShouldReturnEmptyWhenNotFound() {
        Optional<Category> result = adapter.findById(99);
        assertThat(result).isEmpty();
    }

    @Test
    void listPaginatedWithActiveOnlyFalseShouldReturnAllCategories() {
        CategoryEntity entity1 = new CategoryEntity();
        entity1.setId(1);
        entity1.setName("Food");
        entity1.setActive(true);
        jpa.store(1, entity1);

        CategoryEntity entity2 = new CategoryEntity();
        entity2.setId(2);
        entity2.setName("Inactive");
        entity2.setActive(false);
        jpa.store(2, entity2);

        PageResult<Category> result = adapter.listPaginated(0, 10, false);

        assertThat(result.items()).hasSize(2);
        assertThat(result.total()).isEqualTo(2);
    }

    @Test
    void listPaginatedWithActiveOnlyTrueShouldReturnOnlyActiveCategories() {
        CategoryEntity entity1 = new CategoryEntity();
        entity1.setId(1);
        entity1.setName("Food");
        entity1.setActive(true);
        jpa.store(1, entity1);

        CategoryEntity entity2 = new CategoryEntity();
        entity2.setId(2);
        entity2.setName("Inactive");
        entity2.setActive(false);
        jpa.store(2, entity2);

        PageResult<Category> result = adapter.listPaginated(0, 10, true);

        assertThat(result.items()).hasSize(1);
        assertThat(result.items().get(0).name()).isEqualTo("Food");
        assertThat(result.total()).isEqualTo(1);
    }

    @Test
    void updateShouldChangeNameAndReturnUpdatedCategory() {
        CategoryEntity entity = new CategoryEntity();
        entity.setId(1);
        entity.setName("OldName");
        entity.setActive(true);
        jpa.store(1, entity);

        Optional<Category> result = adapter.update(1, "NewName");

        assertThat(result).isPresent();
        assertThat(result.get().name()).isEqualTo("NewName");
    }

    @Test
    void updateShouldReturnEmptyWhenCategoryNotFound() {
        Optional<Category> result = adapter.update(99, "Anything");
        assertThat(result).isEmpty();
    }

    @Test
    void deactivateShouldSetActiveFalseAndReturnTrue() {
        CategoryEntity entity = new CategoryEntity();
        entity.setId(1);
        entity.setActive(true);
        jpa.store(1, entity);

        boolean result = adapter.deactivate(1);

        assertThat(result).isTrue();
        assertThat(entity.isActive()).isFalse();
    }

    @Test
    void deactivateShouldReturnFalseWhenNotFound() {
        boolean result = adapter.deactivate(99);
        assertThat(result).isFalse();
    }

    static class StubJpaCategoryRepository implements JpaCategoryRepository {
        private final Map<Integer, CategoryEntity> store = new HashMap<>();
        private int nextId = 1;
        CategoryEntity lastSavedEntity;

        void store(Integer id, CategoryEntity entity) {
            store.put(id, entity);
        }

        @Override
        public CategoryEntity save(CategoryEntity entity) {
            if (entity.getId() == null) {
                entity.setId(nextId++);
            }
            lastSavedEntity = entity;
            store.put(entity.getId(), entity);
            return entity;
        }

        @Override
        public Optional<CategoryEntity> findById(Integer id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public Page<CategoryEntity> findByActiveTrue(Pageable pageable) {
            List<CategoryEntity> active = store.values().stream()
                .filter(CategoryEntity::isActive)
                .toList();
            return new PageImpl<>(active, pageable, active.size());
        }

        @Override
        public List<CategoryEntity> findByActiveTrue() {
            return store.values().stream()
                .filter(CategoryEntity::isActive)
                .toList();
        }

        @Override
        public Page<CategoryEntity> findAll(Pageable pageable) {
            List<CategoryEntity> all = store.values().stream().toList();
            return new PageImpl<>(all, pageable, all.size());
        }

        @Override
        public void flush() {
            // No-op for stub
        }

        @Override
        public <S extends CategoryEntity> S saveAndFlush(S entity) {
            return (S) save(entity);
        }

        @Override
        public <S extends CategoryEntity> List<S> saveAllAndFlush(Iterable<S> entities) {
            return null;
        }

        @Override
        public void deleteInBatch(Iterable<CategoryEntity> entities) {
            // No-op for stub
        }

        @Override
        public void deleteAllInBatch() {
            // No-op for stub
        }

        @Override
        public void deleteAllInBatch(Iterable<CategoryEntity> entities) {
            // No-op for stub
        }

        @Override
        public void deleteAllByIdInBatch(Iterable<Integer> ids) {
            // No-op for stub
        }

        @Override
        public void deleteAll() {
            // No-op for stub
        }

        @Override
        public void deleteAll(Iterable<? extends CategoryEntity> entities) {
            // No-op for stub
        }

        @Override
        public CategoryEntity getOne(Integer id) {
            return store.get(id);
        }

        @Override
        public CategoryEntity getById(Integer id) {
            return store.get(id);
        }

        @Override
        public CategoryEntity getReferenceById(Integer id) {
            return store.get(id);
        }

        @Override
        public <S extends CategoryEntity> List<S> saveAll(Iterable<S> entities) {
            return null;
        }

        @Override
        public List<CategoryEntity> findAll() {
            return store.values().stream().toList();
        }

        @Override
        public List<CategoryEntity> findAllById(Iterable<Integer> ids) {
            return null;
        }

        @Override
        public long count() {
            return store.size();
        }

        @Override
        public void deleteAllById(Iterable<? extends Integer> ids) {
            // No-op for stub
        }

        @Override
        public void deleteById(Integer id) {
            store.remove(id);
        }

        @Override
        public void delete(CategoryEntity entity) {
            if (entity != null && entity.getId() != null) {
                store.remove(entity.getId());
            }
        }

        @Override
        public boolean existsById(Integer id) {
            return store.containsKey(id);
        }

        @Override
        public <S extends CategoryEntity> boolean exists(org.springframework.data.domain.Example<S> example) {
            return false;
        }

        @Override
        public <S extends CategoryEntity> long count(org.springframework.data.domain.Example<S> example) {
            return 0;
        }

        @Override
        public <S extends CategoryEntity> List<S> findAll(org.springframework.data.domain.Example<S> example) {
            return null;
        }

        @Override
        public <S extends CategoryEntity> List<S> findAll(org.springframework.data.domain.Example<S> example, org.springframework.data.domain.Sort sort) {
            return null;
        }

        @Override
        public <S extends CategoryEntity> Page<S> findAll(org.springframework.data.domain.Example<S> example, Pageable pageable) {
            return null;
        }

        @Override
        public <S extends CategoryEntity> Optional<S> findOne(org.springframework.data.domain.Example<S> example) {
            return Optional.empty();
        }

        @Override
        public List<CategoryEntity> findAll(org.springframework.data.domain.Sort sort) {
            return store.values().stream().toList();
        }

        @Override
        public <S extends CategoryEntity, R> R findBy(org.springframework.data.domain.Example<S> example, java.util.function.Function<org.springframework.data.repository.query.FluentQuery.FetchableFluentQuery<S>, R> queryFunction) {
            return null;
        }
    }
}
