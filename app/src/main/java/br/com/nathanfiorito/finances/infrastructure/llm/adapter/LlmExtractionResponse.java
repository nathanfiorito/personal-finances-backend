package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import com.fasterxml.jackson.annotation.JsonProperty;

class LlmExtractionResponse {
    @JsonProperty("amount")           String amount;
    @JsonProperty("date")             String date;
    @JsonProperty("establishment")    String establishment;
    @JsonProperty("description")      String description;
    @JsonProperty("tax_id")           String taxId;
    @JsonProperty("transaction_type") String transactionType;
    @JsonProperty("payment_method")   String paymentMethod;
    @JsonProperty("confidence")       double confidence;
}
