package br.com.nathanfiorito.finances.infrastructure.config;

import br.com.nathanfiorito.finances.application.category.usecases.CreateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.DeactivateCategoryUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.category.usecases.UpdateCategoryUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.CreateTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.DeleteTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.ListTransactionsUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.UpdateTransactionUseCase;
import br.com.nathanfiorito.finances.domain.category.ports.CategoryRepository;
import br.com.nathanfiorito.finances.domain.transaction.ports.TransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@RequiredArgsConstructor
public class UseCaseConfig {

    private final TransactionRepository transactionRepository;
    private final CategoryRepository categoryRepository;

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
}
