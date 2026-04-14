package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

record LlmCallResult<T>(T content, long inputTokens, long outputTokens, String finishReason) {}
