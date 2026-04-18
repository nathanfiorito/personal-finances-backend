# CLAUDE.md — domain/

## Purpose

Pure business logic. Records, ports (interfaces), enums, exceptions. No Spring annotations, no JPA, no HTTP, no framework imports at all. Enforced by `HexagonalArchitectureTest` (ArchUnit).

## Package Layout

```
domain/
├── transaction/
│   ├── records/      Transaction, TransactionUpdate, ExtractedTransaction, SummaryItem, MonthlyItem, MonthlyCategoryItem
│   ├── enums/        TransactionType (EXPENSE|INCOME), PaymentMethod (CREDIT|DEBIT)
│   ├── ports/        TransactionRepository, LlmPort
│   └── exceptions/   TransactionNotFoundException, LlmExtractionException
├── category/
│   ├── records/      Category
│   ├── ports/        CategoryRepository
│   └── exceptions/   CategoryNotFoundException
├── card/
│   ├── records/      Card, Invoice, InvoiceDailyEntry, InvoicePrediction, InvoiceTimeline
│   ├── ports/        CardRepository, InvoicePredictionRepository
│   ├── exceptions/   CardNotFoundException
│   └── InvoicePeriodCalculator.java   pure domain helper for closing/due-date math
├── invoice/
│   ├── records/      DetectedCard, ExtractedInvoiceItem, InvoiceExtractionRawResult, InvoiceImportPreview
│   ├── ports/        InvoiceExtractorPort, PdfTextExtractorPort
│   └── exceptions/   InvoiceImportException
├── telegram/
│   ├── records/      PendingTransaction
│   └── ports/        NotifierPort, PendingStatePort
└── shared/
    └── PageResult.java   generic paginated result
```

## Rules

- No framework imports. No `org.springframework.*`, no `jakarta.persistence.*`, no `com.fasterxml.jackson.*`. Anything that touches Spring, JPA, HTTP, or serialization belongs in `infrastructure/` or `interfaces/`.
- Records over classes. Domain data types are Java records unless mutability is unavoidable.
- Ports are interfaces, named `<Noun>Port` (outbound, e.g. `LlmPort`) or `<Noun>Repository` (outbound persistence).
- Every exception that crosses a use-case boundary is declared here and mapped in `interfaces/rest/shared/GlobalExceptionHandler.java`.

## When to update this file

- New bounded context → add its subfolder to the Package Layout tree and to the root CLAUDE.md's "What Lives Here" table in the same PR.
- New record / port / enum → add it to the corresponding subfolder listing here.

## Pointers

- Use cases that call these ports live in `application/`.
- Port implementations (adapters) live in `infrastructure/`.
