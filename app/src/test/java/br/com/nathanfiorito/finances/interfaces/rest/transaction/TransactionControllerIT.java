package br.com.nathanfiorito.finances.interfaces.rest.transaction;

import br.com.nathanfiorito.finances.application.transaction.usecases.CreateTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.DeleteTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetTransactionUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.ListTransactionsUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.UpdateTransactionUseCase;
import br.com.nathanfiorito.finances.domain.shared.PageResult;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.TransactionNotFoundException;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TransactionController.class)
class TransactionControllerIT extends BaseControllerIT {

    @MockitoBean private CreateTransactionUseCase createTransaction;
    @MockitoBean private GetTransactionUseCase getTransaction;
    @MockitoBean private ListTransactionsUseCase listTransactions;
    @MockitoBean private UpdateTransactionUseCase updateTransaction;
    @MockitoBean private DeleteTransactionUseCase deleteTransaction;

    private Transaction sampleTransaction() {
        return new Transaction(
            UUID.fromString("00000000-0000-0000-0000-000000000001"),
            new BigDecimal("50.00"),
            LocalDate.of(2024, 6, 15),
            "Supermercado",
            "Weekly groceries",
            1,
            "Food",
            null,
            "text",
            TransactionType.EXPENSE,
            PaymentMethod.CREDIT,
            0.95,
            LocalDateTime.of(2024, 6, 15, 10, 0)
        );
    }

    @Test
    void listShouldReturnPagedTransactionsWhenAuthenticated() throws Exception {
        when(listTransactions.execute(any()))
            .thenReturn(new PageResult<>(List.of(sampleTransaction()), 1));

        mockMvc.perform(get("/api/v1/transactions")
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.items").isArray())
            .andExpect(jsonPath("$.items[0].establishment").value("Supermercado"))
            .andExpect(jsonPath("$.total").value(1));
    }

    @Test
    void listShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(get("/api/v1/transactions"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void getShouldReturnTransactionWhenFound() throws Exception {
        UUID id = UUID.fromString("00000000-0000-0000-0000-000000000001");
        when(getTransaction.execute(any())).thenReturn(sampleTransaction());

        mockMvc.perform(get("/api/v1/transactions/" + id)
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(id.toString()))
            .andExpect(jsonPath("$.amount").value("50.00"));
    }

    @Test
    void getShouldReturnNotFoundWhenTransactionDoesNotExist() throws Exception {
        UUID id = UUID.randomUUID();
        when(getTransaction.execute(any())).thenThrow(new TransactionNotFoundException(id));

        mockMvc.perform(get("/api/v1/transactions/" + id)
                .header("Authorization", validToken()))
            .andExpect(status().isNotFound());
    }

    @Test
    void createShouldReturnCreatedTransactionWhenRequestIsValid() throws Exception {
        when(createTransaction.execute(any())).thenReturn(sampleTransaction());

        mockMvc.perform(post("/api/v1/transactions")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {
                          "amount": 50.00,
                          "category_id": 1,
                          "payment_method": "CREDIT"
                        }
                        """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.establishment").value("Supermercado"));
    }

    @Test
    void createShouldReturnBadRequestWhenRequiredFieldsAreMissing() throws Exception {
        mockMvc.perform(post("/api/v1/transactions")
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void createShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(post("/api/v1/transactions")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"amount": 50.00, "category_id": 1, "payment_method": "CREDIT"}
                        """))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void updateShouldReturnUpdatedTransactionWhenFound() throws Exception {
        UUID id = UUID.fromString("00000000-0000-0000-0000-000000000001");
        when(updateTransaction.execute(any())).thenReturn(sampleTransaction());

        mockMvc.perform(put("/api/v1/transactions/" + id)
                .header("Authorization", validToken())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                        {"amount": 99.99}
                        """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(id.toString()));
    }

    @Test
    void deleteShouldReturnNoContentWhenTransactionExists() throws Exception {
        UUID id = UUID.randomUUID();

        mockMvc.perform(delete("/api/v1/transactions/" + id)
                .header("Authorization", validToken()))
            .andExpect(status().isNoContent());
    }

    @Test
    void deleteShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(delete("/api/v1/transactions/" + UUID.randomUUID()))
            .andExpect(status().isUnauthorized());
    }
}
