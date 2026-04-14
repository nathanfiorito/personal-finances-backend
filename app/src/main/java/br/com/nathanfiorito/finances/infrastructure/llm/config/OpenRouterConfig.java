package br.com.nathanfiorito.finances.infrastructure.llm.config;

import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Tracer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenRouterConfig {

    @Value("${openrouter.api-key}")
    private String apiKey;

    @Bean
    public OpenAIClient openAIClient() {
        return OpenAIOkHttpClient.builder()
            .apiKey(apiKey)
            .baseUrl("https://openrouter.ai/api/v1")
            .build();
    }

    @Bean
    public Tracer llmTracer(OpenTelemetry openTelemetry) {
        return openTelemetry.getTracer("finances-backend.llm");
    }
}
