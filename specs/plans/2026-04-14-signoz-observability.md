# SigNoz Observability Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Instrument the Spring Boot backend with OpenTelemetry to ship distributed traces (HTTP + JDBC + manual LLM spans) and structured logs to a self-hosted SigNoz instance.

**Architecture:** OTel Spring Boot Starter (`io.opentelemetry.instrumentation:opentelemetry-spring-boot-starter`) auto-instruments Spring MVC and JDBC. Manual spans are added to `OpenRouterLlmAdapter` by injecting a `Tracer` bean. Logback is configured with `LogstashEncoder` (JSON stdout) and `OpenTelemetryAppender` (OTLP log bridge to SigNoz).

**Tech Stack:** Java 25, Spring Boot 3.4.5, OpenTelemetry Java Instrumentation BOM 2.15.0, logstash-logback-encoder 8.1, opentelemetry-sdk-testing (test scope)

---

## File Map

| Action | File |
|---|---|
| Modify | `app/pom.xml` |
| Modify | `app/src/main/resources/application.properties` |
| Create | `app/src/main/resources/logback-spring.xml` |
| Modify | `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/config/OpenRouterConfig.java` |
| Create | `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/LlmCallResult.java` |
| Modify | `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapter.java` |
| Modify | `app/src/test/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapterTest.java` |

---

## Task 1: Set up git worktree for the feature branch

**Files:** (git operations only)

- [ ] **Step 1: Create feature branch and worktree**

Run from the `personal-finances-backend` repo root:

```bash
git fetch origin
git worktree add ../personal-finances-backend-signoz -b feature/signoz-observability origin/develop
cd ../personal-finances-backend-signoz
```

This creates a parallel working directory checked out to a new branch `feature/signoz-observability` based on `develop`. All subsequent steps run inside `personal-finances-backend-signoz/`.

- [ ] **Step 2: Verify worktree is on the correct branch**

```bash
git branch
```

Expected: `* feature/signoz-observability`

---

## Task 2: Add OTel dependencies to pom.xml

**Files:**
- Modify: `app/pom.xml`

- [ ] **Step 1: Add the OTel BOM to `<dependencyManagement>`**

Open `app/pom.xml`. Locate the `<dependencyManagement>` section (create it if absent, just before `<dependencies>`). Add:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>io.opentelemetry.instrumentation</groupId>
            <artifactId>opentelemetry-instrumentation-bom</artifactId>
            <version>2.15.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

- [ ] **Step 2: Add the three runtime/test dependencies inside `<dependencies>`**

Add after the existing `<dependency>` blocks (before `</dependencies>`):

```xml
<!-- OpenTelemetry Spring Boot auto-instrumentation (HTTP, JDBC, log bridge) -->
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
</dependency>

<!-- Structured JSON logging to stdout -->
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>8.1</version>
</dependency>

<!-- OTel SDK test utilities (InMemorySpanExporter) -->
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-sdk-testing</artifactId>
    <scope>test</scope>
</dependency>
```

- [ ] **Step 3: Verify the build resolves dependencies without errors**

```bash
cd app && mvn dependency:resolve -q
```

Expected: `BUILD SUCCESS` with no dependency resolution errors.

- [ ] **Step 4: Commit**

```bash
git add app/pom.xml
git commit -m "build: add opentelemetry-spring-boot-starter and logstash-logback-encoder"
```

---

## Task 3: Configure OTel properties and environment variable

**Files:**
- Modify: `app/src/main/resources/application.properties`

- [ ] **Step 1: Add OTel configuration properties**

Append to the end of `application.properties`:

```properties
# OpenTelemetry / SigNoz
otel.service.name=finances-backend
otel.exporter.otlp.endpoint=${SIGNOZ_OTLP_ENDPOINT}
otel.exporter.otlp.protocol=grpc
otel.logs.exporter=otlp
otel.traces.exporter=otlp
otel.metrics.exporter=none
otel.propagators=tracecontext,baggage
```

> **Note on `SIGNOZ_OTLP_ENDPOINT`:** For gRPC, the value must include the port — e.g. `https://signoz-otel.nathanfiorito.com.br:4317`. If the SigNoz reverse proxy terminates at the standard HTTPS port (443) with gRPC-over-TLS configured, omit the port. If you encounter connection issues, switch `otel.exporter.otlp.protocol` to `http/protobuf` and set the endpoint to `https://signoz-otel.nathanfiorito.com.br:4318`.

- [ ] **Step 2: Verify the app starts without the new env var (should fail with a clear error)**

```bash
cd app && mvn spring-boot:run -Dspring-boot.run.jvmArguments="-DSIGNOZ_OTLP_ENDPOINT=missing"
```

Expected: App starts (OTel gracefully handles unreachable endpoints at startup). Stop it with Ctrl+C.

- [ ] **Step 3: Commit**

```bash
git add app/src/main/resources/application.properties
git commit -m "config: add opentelemetry otlp configuration properties"
```

---

## Task 4: Configure Logback with JSON stdout and OTel log bridge

**Files:**
- Create: `app/src/main/resources/logback-spring.xml`

- [ ] **Step 1: Create `logback-spring.xml`**

Create the file `app/src/main/resources/logback-spring.xml` with this content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>

    <!-- Structured JSON to stdout (captured by VPS log aggregator) -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
    </appender>

    <!-- OTel log bridge: forwards every log event to SigNoz via OTLP -->
    <!-- traceId is automatically included, linking logs to their parent trace -->
    <appender name="OTEL"
              class="io.opentelemetry.instrumentation.logback.appender.v1_0.OpenTelemetryAppender">
        <captureExperimentalAttributes>true</captureExperimentalAttributes>
        <captureMdcAttributes>*</captureMdcAttributes>
    </appender>

    <!-- Application code: INFO and above -->
    <logger name="br.com.nathanfiorito.finances" level="INFO"/>

    <!-- Suppress framework noise; SQL is already visible in JDBC traces -->
    <logger name="org.springframework" level="WARN"/>
    <logger name="org.hibernate.SQL" level="WARN"/>
    <logger name="org.hibernate.type.descriptor.sql" level="WARN"/>
    <logger name="com.zaxxer.hikari" level="WARN"/>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="OTEL"/>
    </root>

</configuration>
```

- [ ] **Step 2: Run unit tests to ensure Logback config is valid**

```bash
cd app && mvn test -pl . -q
```

Expected: `BUILD SUCCESS`. A broken `logback-spring.xml` causes all tests to fail at startup.

- [ ] **Step 3: Commit**

```bash
git add app/src/main/resources/logback-spring.xml
git commit -m "feat: configure logback with json stdout and opentelemetry log bridge"
```

---

## Task 5: Add `LlmCallResult` record and refactor `callLlm`

The current `callLlm` discards the full API response after extracting the parsed content. To capture token counts and finish reason for span attributes, `callLlm` must return a richer result.

**Files:**
- Create: `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/LlmCallResult.java`
- Modify: `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapter.java`
- Modify: `app/src/test/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapterTest.java`

- [ ] **Step 1: Write the failing tests — update test overrides to return `LlmCallResult`**

In `OpenRouterLlmAdapterTest`, update both helper methods. The tests will not compile until `LlmCallResult` exists and `callLlm` returns it — that is the expected "red" state.

Replace the two `adapterReturning` helpers and the throw-test:

```java
/** Creates an adapter whose callLlm always returns the given LlmExtractionResponse. */
private OpenRouterLlmAdapter adapterReturning(LlmExtractionResponse response) {
    return new OpenRouterLlmAdapter(null, OpenTelemetry.noop().getTracer("test")) {
        @Override
        @SuppressWarnings("unchecked")
        <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
            return new LlmCallResult<>((T) response, 10L, 5L, "stop");
        }
    };
}

/** Creates an adapter whose callLlm always returns the given LlmDuplicateResponse. */
private OpenRouterLlmAdapter adapterReturningDuplicate(boolean duplicate) {
    return new OpenRouterLlmAdapter(null, OpenTelemetry.noop().getTracer("test")) {
        @Override
        @SuppressWarnings("unchecked")
        <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
            LlmDuplicateResponse r = new LlmDuplicateResponse();
            r.duplicate = duplicate;
            return new LlmCallResult<>((T) r, 10L, 5L, "stop");
        }
    };
}
```

Also update the throw-on-error test (line 183):

```java
@Test
void isDuplicateShouldReturnFalseWhenLlmCallThrows() {
    OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, OpenTelemetry.noop().getTracer("test")) {
        @Override
        <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
            throw new RuntimeException("API unavailable");
        }
    };

    boolean result = adapter.isDuplicate(buildExtracted(), List.of());

    assertThat(result).isFalse();
}
```

Add the import at the top of the test class:

```java
import io.opentelemetry.api.OpenTelemetry;
```

- [ ] **Step 2: Run tests to verify compilation fails (expected red)**

```bash
cd app && mvn test -q 2>&1 | head -30
```

Expected: compilation error mentioning `LlmCallResult` not found or `callLlm` type mismatch.

- [ ] **Step 3: Create `LlmCallResult`**

Create `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/LlmCallResult.java`:

```java
package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

record LlmCallResult<T>(T content, long inputTokens, long outputTokens, String finishReason) {}
```

- [ ] **Step 4: Refactor `callLlm` in `OpenRouterLlmAdapter` to return `LlmCallResult<T>`**

Replace the `callLlm` method (currently lines 94–100):

```java
<T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
    var completion = client.chat().completions().create(params);
    T content = completion.choices().stream()
        .flatMap(choice -> choice.message().content().stream())
        .findFirst()
        .orElseThrow(() -> new LlmExtractionException("Empty response from LLM"));
    long inputTokens = completion.usage()
        .map(u -> u.promptTokens())
        .orElse(0L);
    long outputTokens = completion.usage()
        .map(u -> u.completionTokens())
        .orElse(0L);
    String finishReason = completion.choices().stream()
        .findFirst()
        .flatMap(c -> c.finishReason())
        .map(fr -> fr.toString())
        .orElse("unknown");
    return new LlmCallResult<>(content, inputTokens, outputTokens, finishReason);
}
```

- [ ] **Step 5: Fix callers of `callLlm` in `OpenRouterLlmAdapter` to use `.content()`**

The three private callers (`extractFromText`, `extractFromImage`, `categorize`, `isDuplicate`) currently do `callLlm(params)` and pass the result directly to `mapToExtracted` or compare it. Change each to extract `.content()`:

In `extractFromText` (line ~113):
```java
private ExtractedTransaction extractFromText(String content, String entryType) {
    StructuredChatCompletionCreateParams<LlmExtractionResponse> params =
        ChatCompletionCreateParams.builder()
            .model(HAIKU)
            .addUserMessage(buildTextPrompt(content))
            .responseFormat(LlmExtractionResponse.class, JsonSchemaLocalValidation.NO)
            .build();
    return mapToExtracted(callLlm(params).content(), entryType);
}
```

In `extractFromImage` (line ~119):
```java
private ExtractedTransaction extractFromImage(String base64Content) {
    StructuredChatCompletionCreateParams<LlmExtractionResponse> params =
        buildImageParams(base64Content);
    return mapToExtracted(callLlm(params).content(), "image");
}
```

In `categorize` (line ~55–71):
```java
@Override
public String categorize(ExtractedTransaction extracted, List<String> categoryNames) {
    if (categoryNames.isEmpty()) return "Outros";
    StructuredChatCompletionCreateParams<LlmCategorizeResponse> params =
        ChatCompletionCreateParams.builder()
            .model(HAIKU)
            .addUserMessage(buildCategorizePrompt(extracted, categoryNames))
            .responseFormat(LlmCategorizeResponse.class, JsonSchemaLocalValidation.NO)
            .build();
    try {
        LlmCategorizeResponse response = callLlm(params).content();
        if (response != null && response.category != null
                && categoryNames.contains(response.category)) {
            return response.category;
        }
    } catch (Exception e) {
        // safe default
    }
    return categoryNames.get(0);
}
```

In `isDuplicate` (line ~74–88):
```java
@Override
public boolean isDuplicate(ExtractedTransaction extracted, List<Transaction> recentTransactions) {
    String prompt = buildDuplicatePrompt(extracted, recentTransactions);
    StructuredChatCompletionCreateParams<LlmDuplicateResponse> params =
        ChatCompletionCreateParams.builder()
            .model(HAIKU)
            .addUserMessage(prompt)
            .responseFormat(LlmDuplicateResponse.class, JsonSchemaLocalValidation.NO)
            .build();
    try {
        LlmDuplicateResponse response = callLlm(params).content();
        return response != null && response.duplicate;
    } catch (Exception e) {
        return false;
    }
}
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd app && mvn test -q
```

Expected: `BUILD SUCCESS`. All existing tests should pass — behaviour is identical, only the internal return type changed.

- [ ] **Step 7: Commit**

```bash
git add app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/LlmCallResult.java \
        app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapter.java \
        app/src/test/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapterTest.java
git commit -m "refactor: extract LlmCallResult to capture token counts and finish reason from OpenRouter"
```

---

## Task 6: Add manual LLM spans to `OpenRouterLlmAdapter`

**Files:**
- Modify: `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/config/OpenRouterConfig.java`
- Modify: `app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapter.java`
- Modify: `app/src/test/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapterTest.java`

- [ ] **Step 1: Write failing tests — span assertions**

Add the following two tests to `OpenRouterLlmAdapterTest`. They will fail until `Tracer` is injected and spans are created.

Add these imports to the test class:

```java
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.api.common.AttributeKey;
import java.util.List;
```

Add at the end of `OpenRouterLlmAdapterTest`:

```java
// --- span instrumentation ---

private static Tracer tracerWithExporter(InMemorySpanExporter exporter) {
    SdkTracerProvider provider = SdkTracerProvider.builder()
        .addSpanProcessor(SimpleSpanProcessor.create(exporter))
        .build();
    return provider.get("test");
}

@Test
void extractTransactionShouldCreateSpanWithLlmAttributes() {
    InMemorySpanExporter exporter = InMemorySpanExporter.create();
    Tracer tracer = tracerWithExporter(exporter);

    LlmExtractionResponse response = buildResponse(
        "50.00", "2026-01-15", "Store", null, null, "EXPENSE", null, 0.9
    );
    OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, tracer) {
        @Override
        @SuppressWarnings("unchecked")
        <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
            return new LlmCallResult<>((T) response, 100L, 50L, "stop");
        }
    };

    adapter.extractTransaction("some receipt text", "text");

    List<SpanData> spans = exporter.getFinishedSpanItems();
    assertThat(spans).hasSize(1);
    SpanData span = spans.get(0);
    assertThat(span.getName()).isEqualTo("llm.openrouter/extract");
    assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.model")))
        .isEqualTo("anthropic/claude-haiku-4-5");
    assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.operation")))
        .isEqualTo("extract");
    assertThat(span.getAttributes().get(AttributeKey.longKey("llm.input.tokens")))
        .isEqualTo(100L);
    assertThat(span.getAttributes().get(AttributeKey.longKey("llm.output.tokens")))
        .isEqualTo(50L);
    assertThat(span.getAttributes().get(AttributeKey.stringKey("llm.finish_reason")))
        .isEqualTo("stop");
    assertThat(span.getStatus().getStatusCode()).isEqualTo(StatusCode.UNSET);
}

@Test
void extractTransactionShouldMarkSpanAsErrorWhenLlmThrows() {
    InMemorySpanExporter exporter = InMemorySpanExporter.create();
    Tracer tracer = tracerWithExporter(exporter);

    OpenRouterLlmAdapter adapter = new OpenRouterLlmAdapter(null, tracer) {
        @Override
        <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
            throw new RuntimeException("LLM unavailable");
        }
    };

    assertThatThrownBy(() -> adapter.extractTransaction("text", "text"))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("LLM unavailable");

    SpanData span = exporter.getFinishedSpanItems().get(0);
    assertThat(span.getName()).isEqualTo("llm.openrouter/extract");
    assertThat(span.getStatus().getStatusCode()).isEqualTo(StatusCode.ERROR);
}
```

- [ ] **Step 2: Run tests to verify they fail (expected red)**

```bash
cd app && mvn test -pl . -Dtest=OpenRouterLlmAdapterTest -q 2>&1 | tail -20
```

Expected: compilation error — `OpenRouterLlmAdapter` constructor does not accept `Tracer`.

- [ ] **Step 3: Expose a `Tracer` bean in `OpenRouterConfig`**

The `opentelemetry-spring-boot-starter` auto-configures an `OpenTelemetry` bean. Add a `Tracer` bean to `OpenRouterConfig.java`:

```java
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
```

- [ ] **Step 4: Add `Tracer` field and span wrapping to `OpenRouterLlmAdapter`**

Replace the entire `OpenRouterLlmAdapter.java` with the instrumented version:

```java
package br.com.nathanfiorito.finances.infrastructure.llm.adapter;

import br.com.nathanfiorito.finances.domain.transaction.enums.PaymentMethod;
import br.com.nathanfiorito.finances.domain.transaction.enums.TransactionType;
import br.com.nathanfiorito.finances.domain.transaction.exceptions.LlmExtractionException;
import br.com.nathanfiorito.finances.domain.transaction.ports.LlmPort;
import br.com.nathanfiorito.finances.domain.transaction.records.ExtractedTransaction;
import br.com.nathanfiorito.finances.domain.transaction.records.Transaction;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.openai.client.OpenAIClient;
import com.openai.core.JsonSchemaLocalValidation;
import com.openai.models.chat.completions.ChatCompletionContentPart;
import com.openai.models.chat.completions.ChatCompletionContentPartImage;
import com.openai.models.chat.completions.ChatCompletionContentPartText;
import com.openai.models.chat.completions.ChatCompletionCreateParams;
import com.openai.models.chat.completions.StructuredChatCompletionCreateParams;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Component
@RequiredArgsConstructor
public class OpenRouterLlmAdapter implements LlmPort {

    private static final String HAIKU  = "anthropic/claude-haiku-4-5";
    private static final String SONNET = "anthropic/claude-sonnet-4-6";

    private static final ObjectMapper MAPPER = new ObjectMapper()
        .registerModule(new JavaTimeModule());

    private final OpenAIClient client;
    private final Tracer tracer;

    // -------------------------------------------------------------------------
    // LlmPort
    // -------------------------------------------------------------------------

    @Override
    public ExtractedTransaction extractTransaction(String content, String entryType) {
        String model = "image".equals(entryType) ? SONNET : HAIKU;
        Span span = tracer.spanBuilder("llm.openrouter/extract")
            .setAttribute("llm.model", model)
            .setAttribute("llm.operation", "extract")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            LlmCallResult<LlmExtractionResponse> result = switch (entryType) {
                case "text", "pdf" -> callLlm(
                    ChatCompletionCreateParams.builder()
                        .model(HAIKU)
                        .addUserMessage(buildTextPrompt(content))
                        .responseFormat(LlmExtractionResponse.class, JsonSchemaLocalValidation.NO)
                        .build());
                case "image" -> callLlm(buildImageParams(content));
                default -> throw new IllegalArgumentException(
                    "Unsupported entry type: " + entryType);
            };
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            return mapToExtracted(result.content(), entryType);
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
            throw e;
        } finally {
            span.end();
        }
    }

    @Override
    public String categorize(ExtractedTransaction extracted, List<String> categoryNames) {
        if (categoryNames.isEmpty()) return "Outros";
        Span span = tracer.spanBuilder("llm.openrouter/categorize")
            .setAttribute("llm.model", HAIKU)
            .setAttribute("llm.operation", "categorize")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            StructuredChatCompletionCreateParams<LlmCategorizeResponse> params =
                ChatCompletionCreateParams.builder()
                    .model(HAIKU)
                    .addUserMessage(buildCategorizePrompt(extracted, categoryNames))
                    .responseFormat(LlmCategorizeResponse.class, JsonSchemaLocalValidation.NO)
                    .build();
            LlmCallResult<LlmCategorizeResponse> result = callLlm(params);
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            if (result.content() != null && result.content().category != null
                    && categoryNames.contains(result.content().category)) {
                return result.content().category;
            }
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
        } finally {
            span.end();
        }
        return categoryNames.get(0);
    }

    @Override
    public boolean isDuplicate(ExtractedTransaction extracted, List<Transaction> recentTransactions) {
        Span span = tracer.spanBuilder("llm.openrouter/isDuplicate")
            .setAttribute("llm.model", HAIKU)
            .setAttribute("llm.operation", "isDuplicate")
            .startSpan();
        try (Scope scope = span.makeCurrent()) {
            StructuredChatCompletionCreateParams<LlmDuplicateResponse> params =
                ChatCompletionCreateParams.builder()
                    .model(HAIKU)
                    .addUserMessage(buildDuplicatePrompt(extracted, recentTransactions))
                    .responseFormat(LlmDuplicateResponse.class, JsonSchemaLocalValidation.NO)
                    .build();
            LlmCallResult<LlmDuplicateResponse> result = callLlm(params);
            span.setAttribute("llm.input.tokens", result.inputTokens());
            span.setAttribute("llm.output.tokens", result.outputTokens());
            span.setAttribute("llm.finish_reason", result.finishReason());
            return result.content() != null && result.content().duplicate;
        } catch (Exception e) {
            span.setStatus(StatusCode.ERROR, e.getMessage());
            span.recordException(e);
            return false;
        } finally {
            span.end();
        }
    }

    // -------------------------------------------------------------------------
    // Package-private — overridden by anonymous subclasses in tests
    // -------------------------------------------------------------------------

    <T> LlmCallResult<T> callLlm(StructuredChatCompletionCreateParams<T> params) {
        var completion = client.chat().completions().create(params);
        T content = completion.choices().stream()
            .flatMap(choice -> choice.message().content().stream())
            .findFirst()
            .orElseThrow(() -> new LlmExtractionException("Empty response from LLM"));
        long inputTokens = completion.usage()
            .map(u -> u.promptTokens())
            .orElse(0L);
        long outputTokens = completion.usage()
            .map(u -> u.completionTokens())
            .orElse(0L);
        String finishReason = completion.choices().stream()
            .findFirst()
            .flatMap(c -> c.finishReason())
            .map(fr -> fr.toString())
            .orElse("unknown");
        return new LlmCallResult<>(content, inputTokens, outputTokens, finishReason);
    }

    // -------------------------------------------------------------------------
    // Private: image params builder
    // -------------------------------------------------------------------------

    StructuredChatCompletionCreateParams<LlmExtractionResponse> buildImageParams(String base64Content) {
        ChatCompletionContentPartText textPart = ChatCompletionContentPartText.builder()
            .text(buildImagePrompt())
            .build();
        ChatCompletionContentPartImage imagePart = ChatCompletionContentPartImage.builder()
            .imageUrl(ChatCompletionContentPartImage.ImageUrl.builder()
                .url("data:image/jpeg;base64," + base64Content)
                .build())
            .build();
        return ChatCompletionCreateParams.builder()
            .model(SONNET)
            .addUserMessageOfArrayOfContentParts(List.of(
                ChatCompletionContentPart.ofText(textPart),
                ChatCompletionContentPart.ofImageUrl(imagePart)
            ))
            .responseFormat(LlmExtractionResponse.class, JsonSchemaLocalValidation.NO)
            .build();
    }

    // -------------------------------------------------------------------------
    // Private: mapping
    // -------------------------------------------------------------------------

    private ExtractedTransaction mapToExtracted(LlmExtractionResponse r, String entryType) {
        try {
            BigDecimal amount = new BigDecimal(r.amount);
            LocalDate date = (r.date != null) ? LocalDate.parse(r.date) : LocalDate.now();
            TransactionType transactionType = TransactionType.valueOf(r.transactionType);
            PaymentMethod paymentMethod = (r.paymentMethod != null)
                ? PaymentMethod.valueOf(r.paymentMethod) : null;
            double confidence = (r.confidence != null) ? r.confidence : 0.0;
            return new ExtractedTransaction(
                amount, date, r.establishment, r.description,
                r.taxId, entryType, transactionType, paymentMethod, confidence
            );
        } catch (Exception e) {
            throw new LlmExtractionException("Failed to map LLM response: " + e.getMessage(), e);
        }
    }

    // -------------------------------------------------------------------------
    // Private: prompt builders
    // -------------------------------------------------------------------------

    private String buildTextPrompt(String content) {
        return """
            You are a financial assistant. Extract expense details from the following receipt.

            Receipt:
            %s

            Return a JSON object with these exact fields:
            - amount: transaction amount as a decimal string (e.g. "50.00"), required
            - date: date in YYYY-MM-DD format, or null if not found
            - establishment: merchant or business name, or null
            - description: brief purchase description, or null
            - tax_id: merchant CNPJ (digits only or formatted), or null
            - transaction_type: "EXPENSE" or "INCOME"
            - payment_method: "CREDIT" or "DEBIT", or null if not determinable
            - confidence: your extraction confidence from 0.0 to 1.0
            """.formatted(content);
    }

    private String buildImagePrompt() {
        return """
            You are a financial assistant. Extract expense details from the receipt image.

            Return a JSON object with these exact fields:
            - amount: transaction amount as a decimal string (e.g. "50.00"), required
            - date: date in YYYY-MM-DD format, or null if not found
            - establishment: merchant or business name, or null
            - description: brief purchase description, or null
            - tax_id: merchant CNPJ (digits only or formatted), or null
            - transaction_type: "EXPENSE" or "INCOME"
            - payment_method: "CREDIT" or "DEBIT", or null if not determinable
            - confidence: your extraction confidence from 0.0 to 1.0
            """;
    }

    private String buildCategorizePrompt(ExtractedTransaction extracted, List<String> categoryNames) {
        try {
            String extractedJson = MAPPER.writeValueAsString(extracted);
            return """
                You are a financial assistant. Categorize the following transaction.

                Transaction:
                %s

                Available categories: %s

                Choose the single category that best matches this transaction.
                Return exactly: {"category": "<chosen category name>"}
                You must choose from the available categories list.
                """.formatted(extractedJson, String.join(", ", categoryNames));
        } catch (JsonProcessingException e) {
            throw new LlmExtractionException("Failed to serialize transaction for categorization", e);
        }
    }

    private String buildDuplicatePrompt(ExtractedTransaction extracted,
                                        List<Transaction> recentTransactions) {
        try {
            String extractedJson = MAPPER.writeValueAsString(extracted);
            String recentJson    = MAPPER.writeValueAsString(recentTransactions);
            return """
                You are a financial assistant. Check if the new transaction is a duplicate.

                New transaction:
                %s

                Recent transactions:
                %s

                A duplicate has the same amount, date, and merchant as an existing entry.
                Return exactly: {"duplicate": true} or {"duplicate": false}
                """.formatted(extractedJson, recentJson);
        } catch (JsonProcessingException e) {
            throw new LlmExtractionException(
                "Failed to serialize transactions for duplicate check", e);
        }
    }
}
```

> **Note:** Task 6 Step 4 provides the complete final `OpenRouterLlmAdapter.java`. It supersedes the targeted edits from Task 5 Step 5 — no need to manually reconcile them. Paste the full file as shown.

- [ ] **Step 5: Run all tests**

```bash
cd app && mvn test -q
```

Expected: `BUILD SUCCESS`. All existing tests pass, plus the two new span tests.

- [ ] **Step 6: Commit**

```bash
git add app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/config/OpenRouterConfig.java \
        app/src/main/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapter.java \
        app/src/test/java/br/com/nathanfiorito/finances/infrastructure/llm/adapter/OpenRouterLlmAdapterTest.java
git commit -m "feat: add manual opentelemetry spans to OpenRouterLlmAdapter with llm attributes"
```

---

## Task 7: Run full test suite and open PR

**Files:** (no code changes)

- [ ] **Step 1: Run the full test suite including integration and architecture tests**

```bash
cd app && mvn verify -q
```

Expected: `BUILD SUCCESS`. This runs unit tests, integration tests (Testcontainers — Docker required), and ArchUnit architecture checks.

> **ArchUnit note:** OTel imports (`io.opentelemetry.*`) live only in `infrastructure.llm.adapter` and `infrastructure.llm.config` — no domain or application layer changes were made, so the hexagonal architecture rules will not be violated.

- [ ] **Step 2: Push the branch**

```bash
git push -u origin feature/signoz-observability
```

- [ ] **Step 3: Open a PR to `develop`**

```bash
gh pr create \
  --title "feat: SigNoz observability — OTLP traces and structured logs" \
  --body "$(cat <<'EOF'
## Summary
- Adds OpenTelemetry Spring Boot Starter for auto-instrumentation of HTTP and JDBC
- Configures OTLP export to SigNoz via `SIGNOZ_OTLP_ENDPOINT` env var
- Adds manual LLM spans to `OpenRouterLlmAdapter` with model, token, and finish-reason attributes
- Configures Logback with JSON stdout (`LogstashEncoder`) and OTel log bridge for trace-correlated logs in SigNoz

## New environment variable
`SIGNOZ_OTLP_ENDPOINT` — required. Example: `https://signoz-otel.nathanfiorito.com.br:4317`

## Test plan
- [ ] All unit, integration, and ArchUnit tests pass (`mvn verify`)
- [ ] Deploy to VPS with `SIGNOZ_OTLP_ENDPOINT` set
- [ ] Send a Telegram receipt photo and verify the full trace appears in SigNoz (webhook → JDBC → LLM span)
- [ ] Check SigNoz Log Explorer for correlated logs with `traceId`
- [ ] Verify stdout logs are structured JSON

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
  )" \
  --base develop
```

---

## Environment Variable Checklist (VPS deployment)

Before deploying, add to your VPS environment:

| Variable | Example value | Note |
|---|---|---|
| `SIGNOZ_OTLP_ENDPOINT` | `https://signoz-otel.nathanfiorito.com.br:4317` | gRPC port. Use `:4318` + `http/protobuf` protocol if needed |

All other variables are unchanged.
