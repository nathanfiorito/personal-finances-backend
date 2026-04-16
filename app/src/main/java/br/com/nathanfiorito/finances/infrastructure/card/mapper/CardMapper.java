package br.com.nathanfiorito.finances.infrastructure.card.mapper;

import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.infrastructure.card.entity.CardEntity;

public class CardMapper {

    private CardMapper() {}

    public static Card toDomain(CardEntity entity) {
        return new Card(
            entity.getId(),
            entity.getAlias(),
            entity.getBank(),
            entity.getLastFourDigits(),
            entity.getClosingDay(),
            entity.getDueDay(),
            entity.isActive(),
            entity.getCreatedAt()
        );
    }
}
