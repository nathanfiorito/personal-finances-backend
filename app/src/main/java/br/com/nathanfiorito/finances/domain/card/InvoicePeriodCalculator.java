package br.com.nathanfiorito.finances.domain.card;

import java.time.LocalDate;
import java.time.YearMonth;

public final class InvoicePeriodCalculator {

    private InvoicePeriodCalculator() {}

    public record Period(LocalDate start, LocalDate end) {}

    /**
     * Returns the current invoice period for a given closing day.
     * The period runs from (previous closing + 1) to (current closing).
     */
    public static Period currentPeriod(int closingDay, LocalDate today) {
        LocalDate closingThisMonth = clampDay(today.getYear(), today.getMonthValue(), closingDay);

        if (today.isAfter(closingThisMonth)) {
            // We're past this month's closing — current period ends next month
            LocalDate nextClosing = clampDay(today.getYear(), today.getMonthValue() + 1, closingDay);
            return new Period(closingThisMonth.plusDays(1), nextClosing);
        } else {
            // We're before or on this month's closing — current period ends this month
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
