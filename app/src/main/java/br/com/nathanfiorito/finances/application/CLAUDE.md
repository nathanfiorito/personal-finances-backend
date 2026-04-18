# CLAUDE.md — application/

## Purpose

Use cases. Orchestrate domain records by calling ports. One use case per user-facing action. No framework imports aside from what Spring needs for bean wiring — keep that in `infrastructure/config/UseCaseConfig.java`, not in the use case class itself.

## Package Layout

```
application/
├── transaction/
│   ├── commands/   CreateTransactionCommand, UpdateTransactionCommand, DeleteTransactionCommand
│   ├── queries/    ListTransactionsQuery, GetTransactionQuery, GetSummaryQuery, GetMonthlyQuery, ExportCsvQuery
│   └── usecases/   Create/Update/Delete/Get/List/GetSummary/GetMonthly/ExportCsv TransactionUseCase
├── category/
│   ├── commands/   CreateCategoryCommand, UpdateCategoryCommand, DeactivateCategoryCommand
│   ├── queries/    ListCategoriesQuery
│   └── usecases/   Create/Update/Deactivate/ListCategories UseCase
├── card/
│   ├── commands/   CreateCardCommand, UpdateCardCommand, DeactivateCardCommand
│   ├── queries/    GetCurrentInvoiceQuery, GetInvoiceByMonthQuery, GetInvoiceTimelineQuery
│   └── usecases/   CreateCardUseCase, DeactivateCardUseCase, GetCardUseCase, ListCardsUseCase,
│                   UpdateCardUseCase, GetCurrentInvoiceUseCase, GetInvoiceByMonthUseCase,
│                   GetInvoicePredictionUseCase, GetInvoiceTimelineUseCase, RefreshInvoicePredictionUseCase
├── invoice/
│   ├── commands/   ImportInvoiceCommand
│   └── usecases/   ExtractInvoiceUseCase, ImportInvoiceUseCase
└── telegram/
    ├── commands/   ProcessMessageCommand, ConfirmTransactionCommand, CancelTransactionCommand, ChangeCategoryCommand
    ├── usecases/   ProcessMessageUseCase, ConfirmTransactionUseCase, CancelTransactionUseCase, ChangeCategoryUseCase
    └── AmountFormatter.java   pt-BR currency formatting helper
```

## Conventions

- **Command / Query / UseCase triad.** A command or query is a record that carries inputs. The use case is a class with a single public method (`execute` / `handle`) that takes the command/query.
- **No Spring annotations in use-case classes.** They are plain classes. Wired as beans in `infrastructure/config/UseCaseConfig.java`.
- **Dependencies via constructor.** Ports in, use case out. No field injection.
- **One transaction per use case** when touching persistence. Use Spring's `@Transactional` on the `UseCaseConfig` bean method or wrap at the controller boundary — not inside the use case class.

## Telegram request flow

1. `POST /webhook` → `TelegramWebhookFilter` validates the secret token and chat ID.
2. `TelegramWebhookController` dispatches to a message / command / callback handler.
3. `ProcessMessageUseCase`:
   - Image → Sonnet vision → `ExtractedTransaction`.
   - PDF → PDFBox extracts text → Haiku → `ExtractedTransaction`.
   - Text → Haiku directly.
4. Bot sends inline-keyboard confirmation via `NotifierPort`.
5. Pending state in `InMemoryPendingStateAdapter` (ConcurrentHashMap, 10-min TTL). **Restarts lose pending confirmations by design.**
6. Confirm (callback) → `ConfirmTransactionUseCase` → `LlmPort.isDuplicate()` (Haiku) → `TransactionRepository.save()`.
7. Cancel / change category each have their own use case on the same pending entry.

## Bot commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/ajuda` | List all commands |
| `/relatorio [semana\|anterior\|mes\|MM/AAAA]` | Expense report for a period |
| `/exportar [semana\|anterior\|mes\|MM/AAAA]` | Export expenses as CSV |
| `/categorias` | List active categories |
| `/categorias add <name>` | Add a new category |

## Testing

Prefer stubs over Mockito — every outbound port has a hand-written `Stub*` in `app/src/test/java/br/com/nathanfiorito/finances/stubs/`. Stubs give clearer failure messages and real behaviour; Mockito is reserved for cases where a stub would be more work than it's worth. Inventory: see `../../../test/java/br/com/nathanfiorito/finances/CLAUDE.md`.

## When to update this file

- New use case → add it to the subfolder listing here and, if exposed over HTTP, to the REST controller inventory in `interfaces/CLAUDE.md`.
- New bounded context → add the block to Package Layout.

## Pointers

- Domain records/ports this layer consumes: `../domain/CLAUDE.md`.
- Adapters that implement the ports: `../infrastructure/CLAUDE.md`.
- REST / webhook entry points: `../interfaces/CLAUDE.md`.
