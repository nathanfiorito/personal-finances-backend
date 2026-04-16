package br.com.nathanfiorito.finances.interfaces.rest.card;

import br.com.nathanfiorito.finances.application.card.commands.DeactivateCardCommand;
import br.com.nathanfiorito.finances.application.card.usecases.CreateCardUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.DeactivateCardUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.GetCardUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.ListCardsUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.UpdateCardUseCase;
import br.com.nathanfiorito.finances.domain.card.records.Card;
import br.com.nathanfiorito.finances.interfaces.rest.card.dto.CardResponse;
import br.com.nathanfiorito.finances.interfaces.rest.card.dto.CreateCardRequest;
import br.com.nathanfiorito.finances.interfaces.rest.card.dto.UpdateCardRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("${app.api.base-path}/cards")
@RequiredArgsConstructor
public class CardController {

    private final CreateCardUseCase createCard;
    private final ListCardsUseCase listCards;
    private final GetCardUseCase getCard;
    private final UpdateCardUseCase updateCard;
    private final DeactivateCardUseCase deactivateCard;

    @GetMapping
    public ResponseEntity<List<CardResponse>> list() {
        log.debug("GET /cards");
        List<CardResponse> cards = listCards.execute()
            .stream()
            .map(CardResponse::from)
            .toList();
        log.debug("GET /cards: returned {} items", cards.size());
        return ResponseEntity.ok(cards);
    }

    @GetMapping("/{id}")
    public ResponseEntity<CardResponse> get(@PathVariable int id) {
        log.debug("GET /cards/{}", id);
        Card card = getCard.execute(id);
        return ResponseEntity.ok(CardResponse.from(card));
    }

    @PostMapping
    public ResponseEntity<CardResponse> create(@RequestBody @Valid CreateCardRequest request) {
        log.info("POST /cards: alias={}, bank={}", request.alias(), request.bank());
        Card card = createCard.execute(request.toCommand());
        log.info("POST /cards: created id={}", card.id());
        return ResponseEntity.status(HttpStatus.CREATED).body(CardResponse.from(card));
    }

    @PutMapping("/{id}")
    public ResponseEntity<CardResponse> update(
        @PathVariable int id,
        @RequestBody @Valid UpdateCardRequest request
    ) {
        log.info("PUT /cards/{}: alias={}, bank={}", id, request.alias(), request.bank());
        Card card = updateCard.execute(request.toCommand(id));
        return ResponseEntity.ok(CardResponse.from(card));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deactivate(@PathVariable int id) {
        log.info("DELETE /cards/{}", id);
        deactivateCard.execute(new DeactivateCardCommand(id));
        return ResponseEntity.noContent().build();
    }
}
