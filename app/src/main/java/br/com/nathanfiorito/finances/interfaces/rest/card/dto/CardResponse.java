package br.com.nathanfiorito.finances.interfaces.rest.card.dto;

import br.com.nathanfiorito.finances.domain.card.records.Card;

public record CardResponse(int id, String alias, String bank, String lastFourDigits, int closingDay, int dueDay, boolean isActive) {

    public static CardResponse from(Card card) {
        return new CardResponse(card.id(), card.alias(), card.bank(), card.lastFourDigits(), card.closingDay(), card.dueDay(), card.active());
    }
}
