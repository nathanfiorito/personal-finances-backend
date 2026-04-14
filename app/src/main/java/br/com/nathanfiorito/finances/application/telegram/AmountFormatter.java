package br.com.nathanfiorito.finances.application.telegram;

import java.math.BigDecimal;
import java.text.NumberFormat;
import java.util.Locale;

public final class AmountFormatter {

    private static final Locale PT_BR = Locale.of("pt", "BR");

    private AmountFormatter() {}

    public static String format(BigDecimal amount) {
        NumberFormat fmt = NumberFormat.getNumberInstance(PT_BR);
        fmt.setMinimumFractionDigits(2);
        fmt.setMaximumFractionDigits(2);
        return "R$ " + fmt.format(amount);
    }
}
