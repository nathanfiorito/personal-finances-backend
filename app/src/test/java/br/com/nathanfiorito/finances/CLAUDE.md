# CLAUDE.md — test/

## Purpose

All backend tests. Mirrors the main source layout. JaCoCo coverage gate: **≥80%**, measured at `app/target/site/jacoco/index.html` after `mvn verify`.

## Layout

```
test/java/br/com/nathanfiorito/finances/
├── application/**/usecases/*Test.java        unit tests for use cases (plain JUnit + AssertJ + stubs/)
├── domain/**/Test.java                       domain record / enum tests
├── infrastructure/**/Test.java               pure unit tests (mappers, entities)
├── infrastructure/**/*IT.java                Testcontainers-backed JPA integration tests (extend BaseRepositoryIT)
├── interfaces/rest/**/*IT.java               full Spring Boot @SpringBootTest integration tests (MockMvc, Testcontainers)
├── interfaces/rest/swagger/SwaggerSecurityIT.java   permit-all + toggle behaviour
├── architecture/HexagonalArchitectureTest.java      ArchUnit rules
└── stubs/                                    hand-written doubles (see below)
```

## Naming

- `*Test.java` — unit test (no Spring, no Docker).
- `*IT.java` — integration test (Testcontainers PostgreSQL or full `@SpringBootTest`).

## Stubs over Mockito

Every outbound port has a hand-written stub in `stubs/`. Use these for use-case tests.

| Stub | Implements |
|---|---|
| `StubTransactionRepository` | TransactionRepository |
| `StubCategoryRepository` | CategoryRepository |
| `StubCardRepository` | CardRepository |
| `StubInvoicePredictionRepository` | InvoicePredictionRepository |
| `StubLlmPort` | LlmPort |
| `StubNotifierPort` | NotifierPort |
| `StubPendingStatePort` | PendingStatePort |
| `StubInvoiceExtractorPort` | InvoiceExtractorPort |

Stubs are preferred because they give clearer failure messages, exercise real control flow, and do not break on signature changes the way Mockito mocks do. Use Mockito only when a stub would be more work than it's worth.

## Integration-test bases

- `BaseRepositoryIT.java` — JPA slice + a shared Testcontainers PostgreSQL container. Extend for `infrastructure/**/*IT.java`.
- `BaseControllerIT.java` — full `@SpringBootTest` + MockMvc. Extend for `interfaces/rest/**/*IT.java`.

## Known gap — `mvn verify` does not execute `*IT.java`

The Failsafe plugin is not wired in `pom.xml`, and local Docker is unreliable. Integration tests pass in CI (where Docker + Failsafe are configured), but `mvn verify` on a dev machine currently runs only Surefire (`*Test.java`). Do not rely on `mvn verify` locally to catch integration regressions — run individual `*IT.java` classes explicitly, or wait for CI.

## Standards

- Every change must ship with unit **and** integration tests covering the new/modified code paths.
- Coverage must not drop below **80%**. Check with `mvn verify` (CI) and the JaCoCo report.
- Entity or migration changes require a `*IT.java` that exercises the persistence path.

## Running a single test

```
cd app && mvn test -Dtest=CreateTransactionUseCaseTest
cd app && mvn verify -Dit.test=TransactionControllerIT
```

## When to update this file

- New port → add its `Stub*` to the Stubs table.
- New integration test base → add it under Integration-test bases.

## Pointers

- Use cases under test: `../../../main/java/.../application/CLAUDE.md`.
- Adapters under test: `../../../main/java/.../infrastructure/CLAUDE.md`.
- Architecture rules: `architecture/HexagonalArchitectureTest.java`.
