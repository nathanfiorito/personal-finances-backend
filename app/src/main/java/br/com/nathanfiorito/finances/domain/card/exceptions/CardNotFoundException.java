package br.com.nathanfiorito.finances.domain.card.exceptions;

public class CardNotFoundException extends RuntimeException {
    public CardNotFoundException(int id) {
        super("Card not found: " + id);
    }
}
