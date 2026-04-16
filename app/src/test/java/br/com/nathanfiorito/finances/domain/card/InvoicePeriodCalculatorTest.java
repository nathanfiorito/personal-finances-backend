package br.com.nathanfiorito.finances.domain.card;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class InvoicePeriodCalculatorTest {

    @Test
    void currentPeriodWhenTodayIsAfterClosingDay() {
        // closing_day=15, today=April 20 -> new period: April 16 to May 15
        var result = InvoicePeriodCalculator.currentPeriod(15, LocalDate.of(2026, 4, 20));

        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 4, 16));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 5, 15));
    }

    @Test
    void currentPeriodWhenTodayIsBeforeClosingDay() {
        // closing_day=15, today=April 10 -> period is March 16 to April 15
        var result = InvoicePeriodCalculator.currentPeriod(15, LocalDate.of(2026, 4, 10));

        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 3, 16));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 4, 15));
    }

    @Test
    void currentPeriodWhenTodayIsClosingDay() {
        // closing_day=15, today=April 15 -> period is March 16 to April 15
        var result = InvoicePeriodCalculator.currentPeriod(15, LocalDate.of(2026, 4, 15));

        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 3, 16));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 4, 15));
    }

    @Test
    void currentPeriodWhenTodayIsDayAfterClosing() {
        // closing_day=15, today=April 16 -> NEW period: April 16 to May 15
        var result = InvoicePeriodCalculator.currentPeriod(15, LocalDate.of(2026, 4, 16));

        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 4, 16));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 5, 15));
    }

    @Test
    void clampsClosingDayToEndOfMonth() {
        // closing_day=31, today=Feb 15 -> period is Feb 1 to Feb 28
        var result = InvoicePeriodCalculator.currentPeriod(31, LocalDate.of(2026, 2, 15));

        // Jan 31 is valid, so prev closing = Jan 31, start = Feb 1
        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 2, 1));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 2, 28));
    }

    @Test
    void previousPeriodReturnsOnePeriodBack() {
        // closing_day=15, today=April 20 -> current is Apr 16-May 15, previous is Mar 16-Apr 15
        var result = InvoicePeriodCalculator.previousPeriod(15, LocalDate.of(2026, 4, 20));

        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 3, 16));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 4, 15));
    }

    @Test
    void periodForMonthReturnsSpecificMonth() {
        // closing_day=15, month=March 2026 -> period is Feb 16 to Mar 15
        var result = InvoicePeriodCalculator.periodForMonth(15, 2026, 3);

        assertThat(result.start()).isEqualTo(LocalDate.of(2026, 2, 16));
        assertThat(result.end()).isEqualTo(LocalDate.of(2026, 3, 15));
    }

    @Test
    void dueDateCalculation() {
        // closing_day=15, due_day=25, closing=April 15 -> due=April 25
        var dueDate = InvoicePeriodCalculator.dueDate(25, LocalDate.of(2026, 4, 15));

        assertThat(dueDate).isEqualTo(LocalDate.of(2026, 4, 25));
    }

    @Test
    void dueDateWhenDueDayBeforeClosingDay() {
        // closing_day=25, due_day=5, closing=April 25 -> due=May 5 (next month)
        var dueDate = InvoicePeriodCalculator.dueDate(5, LocalDate.of(2026, 4, 25));

        assertThat(dueDate).isEqualTo(LocalDate.of(2026, 5, 5));
    }
}
