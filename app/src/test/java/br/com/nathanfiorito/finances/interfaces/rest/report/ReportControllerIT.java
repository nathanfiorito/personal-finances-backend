package br.com.nathanfiorito.finances.interfaces.rest.report;

import br.com.nathanfiorito.finances.application.transaction.usecases.ExportCsvUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetMonthlyUseCase;
import br.com.nathanfiorito.finances.application.transaction.usecases.GetSummaryUseCase;
import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyCategoryItem;
import br.com.nathanfiorito.finances.domain.transaction.records.MonthlyItem;
import br.com.nathanfiorito.finances.domain.transaction.records.SummaryItem;
import br.com.nathanfiorito.finances.interfaces.rest.BaseControllerIT;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;

import java.math.BigDecimal;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ReportController.class)
class ReportControllerIT extends BaseControllerIT {

    @MockBean private GetSummaryUseCase getSummary;
    @MockBean private GetMonthlyUseCase getMonthly;
    @MockBean private ExportCsvUseCase exportCsv;

    @Test
    void summaryShouldReturnItemsGroupedByCategoryWhenAuthenticated() throws Exception {
        when(getSummary.execute(any()))
            .thenReturn(List.of(new SummaryItem("Food", new BigDecimal("150.00"), 3)));

        mockMvc.perform(get("/api/v1/reports/summary")
                .param("start", "2024-06-01")
                .param("end", "2024-06-30")
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].category").value("Food"))
            .andExpect(jsonPath("$[0].total").value(150.00))
            .andExpect(jsonPath("$[0].count").value(3));
    }

    @Test
    void summaryShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(get("/api/v1/reports/summary")
                .param("start", "2024-06-01")
                .param("end", "2024-06-30"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void summaryShouldReturnBadRequestWhenDatesAreMissing() throws Exception {
        mockMvc.perform(get("/api/v1/reports/summary")
                .header("Authorization", validToken()))
            .andExpect(status().isBadRequest());
    }

    @Test
    void monthlyShouldReturnMonthlyBreakdownWhenAuthenticated() throws Exception {
        when(getMonthly.execute(any()))
            .thenReturn(List.of(new MonthlyItem(
                6,
                new BigDecimal("200.00"),
                List.of(new MonthlyCategoryItem("Food", new BigDecimal("200.00")))
            )));

        mockMvc.perform(get("/api/v1/reports/monthly")
                .param("year", "2024")
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].month").value(6))
            .andExpect(jsonPath("$[0].by_category[0].category").value("Food"));
    }

    @Test
    void monthlyShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(get("/api/v1/reports/monthly")
                .param("year", "2024"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void exportCsvShouldReturnCsvFileWhenAuthenticated() throws Exception {
        byte[] csvContent = "id,amount,date\n".getBytes();
        when(exportCsv.execute(any())).thenReturn(csvContent);

        mockMvc.perform(get("/api/v1/export/csv")
                .param("start", "2024-06-01")
                .param("end", "2024-06-30")
                .header("Authorization", validToken()))
            .andExpect(status().isOk())
            .andExpect(header().string("Content-Type", "text/csv;charset=UTF-8"))
            .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString("attachment")))
            .andExpect(content().bytes(csvContent));
    }

    @Test
    void exportCsvShouldReturnUnauthorizedWhenTokenIsMissing() throws Exception {
        mockMvc.perform(get("/api/v1/export/csv")
                .param("start", "2024-06-01")
                .param("end", "2024-06-30"))
            .andExpect(status().isUnauthorized());
    }
}
