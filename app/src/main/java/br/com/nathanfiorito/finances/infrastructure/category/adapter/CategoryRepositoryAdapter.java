package br.com.nathanfiorito.finances.infrastructure.category.adapter;

import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import br.com.nathanfiorito.finances.infrastructure.category.mapper.CategoryMapper;
import br.com.nathanfiorito.finances.infrastructure.category.repository.JpaCategoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CategoryRepositoryAdapter implements CategoryRepository {

    private final JpaCategoryRepository jpa;

    @Override
    @Transactional
    public Category save(String name) {
        CategoryEntity entity = new CategoryEntity();
        entity.setName(name);
        entity.setActive(true);
        return CategoryMapper.toDomain(jpa.save(entity));
    }

    @Override
    public List<Category> listAll() {
        return jpa.findByActiveTrue().stream().map(CategoryMapper::toDomain).toList();
    }

    @Override
    public Optional<Category> findById(int id) {
        return jpa.findById(id).map(CategoryMapper::toDomain);
    }

    @Override
    public PageResult<Category> listPaginated(int page, int pageSize, boolean activeOnly) {
        PageRequest pageable = PageRequest.of(page, pageSize);
        Page<CategoryEntity> result = activeOnly
            ? jpa.findByActiveTrue(pageable)
            : jpa.findAll(pageable);
        return new PageResult<>(
            result.getContent().stream().map(CategoryMapper::toDomain).toList(),
            (int) result.getTotalElements()
        );
    }

    @Override
    @Transactional
    public Optional<Category> update(int id, String name) {
        return jpa.findById(id).map(entity -> {
            entity.setName(name);
            return CategoryMapper.toDomain(jpa.save(entity));
        });
    }

    @Override
    @Transactional
    public boolean deactivate(int id) {
        return jpa.findById(id).map(entity -> {
            entity.setActive(false);
            jpa.save(entity);
            return true;
        }).orElse(false);
    }
}
