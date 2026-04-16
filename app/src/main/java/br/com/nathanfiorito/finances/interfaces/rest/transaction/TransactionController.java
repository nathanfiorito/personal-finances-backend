package br.com.nathanfiorito.finances.interfaces.rest.transaction;

import br.com.nathanfiorito.finances.application.transaction.commands.DeleteTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.queries.GetTransactionQuery;
import br.com.nathanfiorito.finances.application.transaction.queries.ListTransactionsQuery;
import br.com.nathanfiorito.finances.application.transaction.usecases.CreateTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.DeleteTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.ListTransactionsUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.UpdateTransactionUseCase;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.interfaces.rest.shared.PageResponse;
import br.com.nathanfiorito.finances.interfaces.rest.transaction.dto.CreateTransactionRequest;
import br.com.nathanfiorito.finances.interfaces.rest.transaction.dto.TransactionResponse;
import br.com.nathanfiorito.finances.interfaces.rest.transaction.dto.UpdateTransactionRequest;
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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("${app.api.base-path}/transactions")
@RequiredArgsConstructor
public class TransactionController {

    private final CreateTransactionUseCase createTransaction;
    private final GetTransactionUseCase getTransaction;
    private final ListTransactionsUseCase listTransactions;
    private final UpdateTransactionUseCase updateTransaction;
    private final DeleteTransactionUseCase deleteTransaction;

    @GetMapping
    public ResponseEntity<PageResponse<TransactionResponse>> list(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(name = "page_size", defaultValue = "20") int pageSize
    ) {
        log.debug("GET /transactions: page={}, pageSize={}", page, pageSize);
        PageResult<Transaction> result = listTransactions.execute(new ListTransactionsQuery(page, pageSize));
        log.debug("GET /transactions: returned {} items, total={}", result.items().size(), result.total());
        return ResponseEntity.ok(PageResponse.from(result, TransactionResponse::from, page, pageSize));
    }

    @GetMapping("/{id}")
    public ResponseEntity<TransactionResponse> get(@PathVariable UUID id) {
        log.debug("GET /transactions/{}", id);
        Transaction tx = getTransaction.execute(new GetTransactionQuery(id));
        return ResponseEntity.ok(TransactionResponse.from(tx));
    }

    @PostMapping
    public ResponseEntity<TransactionResponse> create(@RequestBody @Valid CreateTransactionRequest request) {
        log.info("POST /transactions: creating transaction");
        Transaction tx = createTransaction.execute(request.toCommand());
        log.info("POST /transactions: created id={}", tx.id());
        return ResponseEntity.status(HttpStatus.CREATED).body(TransactionResponse.from(tx));
    }

    @PutMapping("/{id}")
    public ResponseEntity<TransactionResponse> update(
        @PathVariable UUID id,
        @RequestBody @Valid UpdateTransactionRequest request
    ) {
        log.info("PUT /transactions/{}: updating", id);
        Transaction tx = updateTransaction.execute(request.toCommand(id));
        return ResponseEntity.ok(TransactionResponse.from(tx));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        log.info("DELETE /transactions/{}", id);
        deleteTransaction.execute(new DeleteTransactionCommand(id));
        return ResponseEntity.noContent().build();
    }
}
