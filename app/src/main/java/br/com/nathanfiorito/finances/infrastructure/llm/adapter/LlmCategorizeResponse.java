package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import com.fasterxml.jackson.annotation.JsonProperty;

class LlmCategorizeResponse {
    @JsonProperty("category") String category;
}
