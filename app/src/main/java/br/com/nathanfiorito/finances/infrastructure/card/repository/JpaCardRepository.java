package br.com.nathanfiorito.finances.infrastructure.card.repository;

import br.com.nathanfiorito.finances.infrastructure.card.entity.CardEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface JpaCardRepository extends JpaRepository<CardEntity, Integer> {
    List<CardEntity> findByActiveTrue();
}
