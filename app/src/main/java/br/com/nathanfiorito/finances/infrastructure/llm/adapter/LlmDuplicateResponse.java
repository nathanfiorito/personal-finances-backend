package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import com.fasterxml.jackson.annotation.JsonProperty;

class LlmDuplicateResponse {
    @JsonProperty("duplicate") boolean duplicate;
}
