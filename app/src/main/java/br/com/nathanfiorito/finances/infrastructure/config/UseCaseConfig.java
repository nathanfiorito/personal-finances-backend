package br.com.nathanfiorito.finances.infrastructure.config;

import br.com.nathanfiorito.finances.application.card.usecases.CreateCardUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.DeactivateCardUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.GetCardUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.ListCardsUseCase;
import br.com.nathanfiorito.finances.application.card.usecases.UpdateCardUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.CreateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.DeactivateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.UpdateCategoryUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.CancelTransactionUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.ChangeCategoryUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.ConfirmTransactionUseCase;
import br.com.nathanfiorito.finances.application.telegram.usecases.ProcessMessageUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.CreateTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.DeleteTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.ExportCsvUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetMonthlyUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetSummaryUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.ListTransactionsUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.UpdateTransactionUseCase;
import br.com.nathanfiorito.finances.domain.card.ports.CardRepository;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;
import br.com.nathanfiorito.finances.domain.telegram.ports.PendingStatePort;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@RequiredArgsConstructor
public class UseCaseConfig {

    private final TransactionRepository transactionRepository;
    private final CategoryRepository categoryRepository;
    private final CardRepository cardRepository;
    private final LlmPort llmPort;
    private final NotifierPort notifierPort;
    private final PendingStatePort pendingStatePort;

    @Bean
    public CreateTransactionUseCase createTransactionUseCase() {
        return new CreateTransactionUseCase(transactionRepository);
    }

    @Bean
    public GetTransactionUseCase getTransactionUseCase() {
        return new GetTransactionUseCase(transactionRepository);
    }

    @Bean
    public ListTransactionsUseCase listTransactionsUseCase() {
        return new ListTransactionsUseCase(transactionRepository);
    }

    @Bean
    public UpdateTransactionUseCase updateTransactionUseCase() {
        return new UpdateTransactionUseCase(transactionRepository);
    }

    @Bean
    public DeleteTransactionUseCase deleteTransactionUseCase() {
        return new DeleteTransactionUseCase(transactionRepository);
    }

    @Bean
    public GetSummaryUseCase getSummaryUseCase() {
        return new GetSummaryUseCase(transactionRepository);
    }

    @Bean
    public GetMonthlyUseCase getMonthlyUseCase() {
        return new GetMonthlyUseCase(transactionRepository);
    }

    @Bean
    public ExportCsvUseCase exportCsvUseCase() {
        return new ExportCsvUseCase(transactionRepository);
    }

    @Bean
    public CreateCategoryUseCase createCategoryUseCase() {
        return new CreateCategoryUseCase(categoryRepository);
    }

    @Bean
    public ListCategoriesUseCase listCategoriesUseCase() {
        return new ListCategoriesUseCase(categoryRepository);
    }

    @Bean
    public UpdateCategoryUseCase updateCategoryUseCase() {
        return new UpdateCategoryUseCase(categoryRepository);
    }

    @Bean
    public DeactivateCategoryUseCase deactivateCategoryUseCase() {
        return new DeactivateCategoryUseCase(categoryRepository);
    }

    // -------------------------------------------------------------------------
    // Card use cases
    // -------------------------------------------------------------------------

    @Bean
    public CreateCardUseCase createCardUseCase() {
        return new CreateCardUseCase(cardRepository);
    }

    @Bean
    public ListCardsUseCase listCardsUseCase() {
        return new ListCardsUseCase(cardRepository);
    }

    @Bean
    public GetCardUseCase getCardUseCase() {
        return new GetCardUseCase(cardRepository);
    }

    @Bean
    public UpdateCardUseCase updateCardUseCase() {
        return new UpdateCardUseCase(cardRepository);
    }

    @Bean
    public DeactivateCardUseCase deactivateCardUseCase() {
        return new DeactivateCardUseCase(cardRepository);
    }

    // -------------------------------------------------------------------------
    // Telegram use cases
    // -------------------------------------------------------------------------

    @Bean
    public ProcessMessageUseCase processMessageUseCase() {
        return new ProcessMessageUseCase(llmPort, categoryRepository, pendingStatePort, notifierPort);
    }

    @Bean
    public ConfirmTransactionUseCase confirmTransactionUseCase() {
        return new ConfirmTransactionUseCase(transactionRepository, llmPort, pendingStatePort, notifierPort);
    }

    @Bean
    public CancelTransactionUseCase cancelTransactionUseCase() {
        return new CancelTransactionUseCase(pendingStatePort, notifierPort);
    }

    @Bean
    public ChangeCategoryUseCase changeCategoryUseCase() {
        return new ChangeCategoryUseCase(pendingStatePort, notifierPort);
    }
}
