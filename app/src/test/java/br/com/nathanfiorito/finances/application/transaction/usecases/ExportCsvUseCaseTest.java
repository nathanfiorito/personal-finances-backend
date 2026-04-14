package br.com.nathanfiorito.finances.application.transaction.usecases;

import br.com.nathanfiorito.finances.application.transaction.commands.CreateTransactionCommand;
import br.com.nathanfiorito.finances.application.transaction.queries.ExportCsvQuery;
import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.stubs.StubTransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class ExportCsvUseCaseTest {

    private StubTransactionRepository repository;
    private ExportCsvUseCase useCase;
    private CreateTransactionUseCase createUseCase;

    private static final LocalDate START = LocalDate.of(2025, 1, 1);
    private static final LocalDate END   = LocalDate.of(2025, 1, 31);

    @BeforeEach
    void setUp() {
        repository = new StubTransactionRepository();
        useCase = new ExportCsvUseCase(repository);
        createUseCase = new CreateTransactionUseCase(repository);
    }

    @Test
    void shouldIncludeBomAndHeader() {
        byte[] csv = useCase.execute(new ExportCsvQuery(START, END));
        String content = new String(csv, StandardCharsets.UTF_8);

        assertThat(content).startsWith("\uFEFF");
        assertThat(content).contains("date,amount,establishment,category,description,tax_id,entry_type,transaction_type");
    }

    @Test
    void shouldWriteOneRowPerTransaction() {
        createUseCase.execute(new CreateTransactionCommand(
            new BigDecimal("99.90"), LocalDate.of(2025, 1, 10),
            1, "text", TransactionType.EXPENSE, PaymentMethod.CREDIT,
            "Supermarket", "Groceries", "12345678000195", 0.95
        ));

        byte[] csv = useCase.execute(new ExportCsvQuery(START, END));
        String content = new String(csv, StandardCharsets.UTF_8);
        String[] lines = content.split("\n", -1);

        assertThat(lines).hasSize(3); // BOM+header line, data line, trailing empty
        assertThat(lines[1]).contains("2025-01-10");
        assertThat(lines[1]).contains("99.90");
        assertThat(lines[1]).contains("Supermarket");
        assertThat(lines[1]).contains("expense");
    }

    @Test
    void shouldEscapeFieldsContainingCommas() {
        createUseCase.execute(new CreateTransactionCommand(
            new BigDecimal("10.00"), LocalDate.of(2025, 1, 5),
            1, "text", TransactionType.EXPENSE, PaymentMethod.DEBIT,
            "Store, Inc.", null, null, 0.9
        ));

        byte[] csv = useCase.execute(new ExportCsvQuery(START, END));
        String content = new String(csv, StandardCharsets.UTF_8);

        assertThat(content).contains("\"Store, Inc.\"");
    }

    @Test
    void shouldReturnOnlyHeaderForEmptyPeriod() {
        byte[] csv = useCase.execute(new ExportCsvQuery(START, END));
        String content = new String(csv, StandardCharsets.UTF_8);
        String[] lines = content.split("\n", -1);

        assertThat(lines).hasSize(2); // BOM+header, trailing empty
    }
}
