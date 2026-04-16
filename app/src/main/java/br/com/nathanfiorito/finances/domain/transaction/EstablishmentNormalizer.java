package br.com.nathanfiorito.finances.domain.transaction;

import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

public class EstablishmentNormalizer {

    private static final Set<String> STOPWORDS = Set.of("DE", "DO", "DA", "E");
    private static final int PREFIX_LENGTH = 4;
    private static final Pattern NON_ALNUM = Pattern.compile("[^A-Z0-9 ]");
    private static final Pattern DIGITS = Pattern.compile("\\d+");
    private static final Pattern WHITESPACE = Pattern.compile("\\s+");
    private static final double JACCARD_THRESHOLD = 0.5;

    public boolean areSameEstablishment(String a, String b) {
        if (a == null || b == null) return false;
        Set<String> tokensA = significantTokens(a);
        Set<String> tokensB = significantTokens(b);
        if (tokensA.isEmpty() || tokensB.isEmpty()) return false;

        String prefixA = firstTokenPrefix(tokensA);
        String prefixB = firstTokenPrefix(tokensB);
        if (prefixA != null && prefixA.equals(prefixB)) return true;

        return jaccard(tokensA, tokensB) >= JACCARD_THRESHOLD;
    }

    private Set<String> significantTokens(String raw) {
        String upper = raw.toUpperCase();
        String cleaned = NON_ALNUM.matcher(upper).replaceAll(" ");
        cleaned = DIGITS.matcher(cleaned).replaceAll(" ");
        cleaned = WHITESPACE.matcher(cleaned).replaceAll(" ").trim();
        Set<String> tokens = new HashSet<>();
        for (String tok : cleaned.split(" ")) {
            if (tok.length() >= 3 && !STOPWORDS.contains(tok)) {
                tokens.add(tok);
            }
            if (tokens.size() == 2) break;
        }
        return tokens;
    }

    private String firstTokenPrefix(Set<String> tokens) {
        return tokens.stream()
            .sorted()
            .findFirst()
            .filter(t -> t.length() >= PREFIX_LENGTH)
            .map(t -> t.substring(0, PREFIX_LENGTH))
            .orElse(null);
    }

    private double jaccard(Set<String> a, Set<String> b) {
        Set<String> union = new HashSet<>(a);
        union.addAll(b);
        Set<String> intersection = new HashSet<>(a);
        intersection.retainAll(b);
        return union.isEmpty() ? 0.0 : (double) intersection.size() / union.size();
    }
}
