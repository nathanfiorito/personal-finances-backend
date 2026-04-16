package br.com.nathanfiorito.finances.domain.card;

import java.time.LocalDate;
import java.time.YearMonth;

public final class InvoicePeriodCalculator {

    private InvoicePeriodCalculator() {}

    public record Period(LocalDate start, LocalDate end) {}

    /**
     * Returns the current invoice period for a given closing day.
     * The period runs from (previous closing + 1) to (current closing).
     * A new period begins exactly on the day after the closing date; on any
     * other day (before, on, or more than one day after closing) the period
     * that ends on this month's closing date is returned.
     */
    public static Period currentPeriod(int closingDay, LocalDate today) {
        LocalDate closingThisMonth = clampDay(today.getYear(), today.getMonthValue(), closingDay);

        if (today.equals(closingThisMonth.plusDays(1))) {
            // Exactly the first day of the new cycle — return the new period
            LocalDate nextClosing = clampDay(today.getYear(), today.getMonthValue() + 1, closingDay);
            return new Period(today, nextClosing);
        } else {
            // Before closing, on closing, or more than one day after closing — return the period ending this month
            LocalDate prevClosing = clampDay(today.getYear(), today.getMonthValue() - 1, closingDay);
            return new Period(prevClosing.plusDays(1), closingThisMonth);
        }
    }

    /**
     * Returns the previous invoice period (one cycle before current).
     */
    public static Period previousPeriod(int closingDay, LocalDate today) {
        Period current = currentPeriod(closingDay, today);
        LocalDate prevEnd = current.start().minusDays(1);
        LocalDate prevClosing = clampDay(prevEnd.getYear(), prevEnd.getMonthValue() - 1, closingDay);
        return new Period(prevClosing.plusDays(1), prevEnd);
    }

    /**
     * Returns the invoice period that closes in the given year/month.
     */
    public static Period periodForMonth(int closingDay, int year, int month) {
        LocalDate closing = clampDay(year, month, closingDay);
        LocalDate prevClosing = clampDay(year, month - 1, closingDay);
        return new Period(prevClosing.plusDays(1), closing);
    }

    /**
     * Calculates the due date relative to a closing date.
     * If dueDay <= closingDay of closing's month, due is next month.
     */
    public static LocalDate dueDate(int dueDay, LocalDate closingDate) {
        if (dueDay <= closingDate.getDayOfMonth()) {
            return clampDay(closingDate.getYear(), closingDate.getMonthValue() + 1, dueDay);
        }
        return clampDay(closingDate.getYear(), closingDate.getMonthValue(), dueDay);
    }

    private static LocalDate clampDay(int year, int month, int day) {
        // Normalize month overflow/underflow
        LocalDate base = LocalDate.of(year, 1, 1).plusMonths(month - 1);
        YearMonth ym = YearMonth.of(base.getYear(), base.getMonth());
        int clamped = Math.min(day, ym.lengthOfMonth());
        return ym.atDay(clamped);
    }
}
