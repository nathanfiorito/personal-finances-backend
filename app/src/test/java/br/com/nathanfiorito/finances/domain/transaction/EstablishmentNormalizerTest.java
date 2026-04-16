package br.com.nathanfiorito.finances.domain.transaction;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class EstablishmentNormalizerTest {

    private final EstablishmentNormalizer normalizer = new EstablishmentNormalizer();

    @Test
    void sameBrandDifferentStoreNumbersMatch() {
        assertThat(normalizer.areSameEstablishment("RAIA 4076", "RAIA 1783")).isTrue();
    }

    @Test
    void uberTripVariantsMatch() {
        assertThat(normalizer.areSameEstablishment("UBER* TRIP", "Uber UBER *TRIP HELP.U")).isTrue();
    }

    @Test
    void hirotaVariantsMatch() {
        assertThat(normalizer.areSameEstablishment("HIROTA OFFICE CEIC ITA", "HIROTA OFFICE CEIC ITA")).isTrue();
    }

    @Test
    void prefixedIfoodMatchesIfoodHome() {
        assertThat(normalizer.areSameEstablishment("IFD*IFOOD CLUBOsasco BRA", "IFD*IFOOD CLUB OSASCO")).isTrue();
    }

    @Test
    void differentBrandsDoNotMatch() {
        assertThat(normalizer.areSameEstablishment("APPLE.COM/BILL", "Google YouTubePremium")).isFalse();
    }

    @Test
    void drogariaVariantsMatch() {
        assertThat(normalizer.areSameEstablishment("DROGARIA SAO PAULO", "DROGARIA SAO PAULO 325")).isTrue();
    }

    @Test
    void completelyDifferentMerchantsDoNotMatch() {
        assertThat(normalizer.areSameEstablishment("RENNER 537 SHOPPING IB", "RAIA 4076")).isFalse();
    }

    @Test
    void nullSafeOnBothSides() {
        assertThat(normalizer.areSameEstablishment(null, "X")).isFalse();
        assertThat(normalizer.areSameEstablishment("X", null)).isFalse();
        assertThat(normalizer.areSameEstablishment(null, null)).isFalse();
    }

    @Test
    void emptyStringsDoNotMatch() {
        assertThat(normalizer.areSameEstablishment("", "")).isFalse();
    }

    @Test
    void openaiVariantsMatch() {
        assertThat(normalizer.areSameEstablishment("OPENAI *CHATGPT SUBSCR", "OPENAI CHATGPT")).isTrue();
    }
}
