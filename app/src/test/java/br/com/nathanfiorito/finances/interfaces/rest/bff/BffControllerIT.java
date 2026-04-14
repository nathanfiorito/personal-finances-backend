package br.com.nathanfiorito.finances.interfaces.rest.bff;

import br.com.nathanfiorito.finances.application.category.usecases.ListCategoriesUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.ListTransactionsUseCase;
import br.com.nathanfiorito.finances.domain.category.records.Category;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(BffController.class)
class BffControllerIT extends BaseControllerIT {

    @MockitoBean private ListTransactionsUseCase listTransactions;
    @MockitoBean private ListCategoriesUseCase listCategories;

    @Test
    void getTransactionsShouldReturnCombinedResponseWhenAuthenticated() throws Exception {
        Transaction tx = new Transaction(
            UUID.randomUUID(),
            new BigDecimal("75.00"),
            LocalDate.of(2024, 6, 10),
            "Padaria",
            "Bread",
            2,
            "Alimentação",
            null,
            "text",
            TransactionType.EXPENSE,
            PaymentMethod.DEBIT,
            1.0,
            LocalDateTime.of(2024, 6, 10, 9, 0)
        );
        Category cat = new Category(2, "Alimentação", true);

        when(listTransactions.execute(any())).thenReturn(new PageResult<>(List.of(tx), 1));
        when(listCategories.execute(any())).thenReturn(new PageResult<>(List.of(cat), 1));

        mockMvc.perform(get("/api/v1/bff/transactions")
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.transactions.items[0].establishment").value("Padaria"))
            .andExpect(jsonPath("$.categories[0].name").value("Alimentação"));
    }

    @Test
    void getTransactionsShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(get("/api/v1/bff/transactions"))
            .andExpect(status().isUnauthorized());
    }
}
