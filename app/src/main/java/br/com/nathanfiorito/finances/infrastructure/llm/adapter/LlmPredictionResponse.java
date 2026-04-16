package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import com.fasterxml.jackson.annotation.JsonProperty;

class LlmPredictionResponse {
    @JsonProperty("predicted_total")      String predictedTotal;
    @JsonProperty("confidence")           String confidence;
    @JsonProperty("projected_remaining")  String projectedRemaining;
    @JsonProperty("based_on_invoices")    int basedOnInvoices;
}
