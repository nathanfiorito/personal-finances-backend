package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/** Raw JSON payload returned by Haiku for invoice extraction. Fields mirror the prompt's schema. */
public class LlmInvoiceExtractionResponse {

    @JsonProperty("card_last_four_digits")
    public String cardLastFourDigits;

    @JsonProperty("items")
    public List<Item> items;

    public static class Item {
        @JsonProperty("date")              public String date;
        @JsonProperty("establishment")     public String establishment;
        @JsonProperty("description")       public String description;
        @JsonProperty("amount")            public String amount;
        @JsonProperty("suggested_category_id")   public Integer suggestedCategoryId;
        @JsonProperty("suggested_category_name") public String suggestedCategoryName;
        @JsonProperty("issuer_hint")       public String issuerHint;
        @JsonProperty("is_international")  public Boolean isInternational;
        @JsonProperty("original_currency") public String originalCurrency;
        @JsonProperty("original_amount")   public String originalAmount;
        @JsonProperty("confidence")        public Double confidence;
    }
}
