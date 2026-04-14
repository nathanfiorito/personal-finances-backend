package br.com.nathanfiorito.finances.infrastructure.category.repository;

import br.com.nathanfiorito.finances.infrastructure.category.entity.CategoryEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface JpaCategoryRepository extends JpaRepository<CategoryEntity, Integer> {
    Page<CategoryEntity> findByActiveTrue(Pageable pageable);
    List<CategoryEntity> findByActiveTrue();
}
