# Personal Finances — Java API

Spring Boot REST API and Telegram bot for personal expense tracking.

**Stack:** Java 25 · Spring Boot 3.x · Maven · PostgreSQL (Flyway) · JUnit 5 + Testcontainers

---

## Prerequisites

- Java 25+
- Maven 3.9+
- Docker (for local PostgreSQL and/or integration tests)

---

## Step-by-step local setup

### 1. Start a local PostgreSQL instance

```bash
docker run -d \
  --name finances-db \
  -e POSTGRES_DB=finances \
  -e POSTGRES_USER=finances \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  postgres:16
```

### 2. Set environment variables

Export the variables below in your shell, or create a `.env` file and load it with `export $(grep -v '^#' .env | xargs)`.

See the [Environment Variables](#environment-variables) table for descriptions.

```bash
export DB_URL=jdbc:postgresql://localhost:5432/finances
export DB_USERNAME=finances
export DB_PASSWORD=secret

export JWT_SECRET=$(openssl rand -base64 32)

export APP_ADMIN_EMAIL=admin@example.com
export APP_ADMIN_PASSWORD_HASH='$2a$10$...'   # see below

export OPENROUTER_API_KEY=sk-or-...

export TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
export TELEGRAM_WEBHOOK_SECRET=any-random-string
export TELEGRAM_ALLOWED_CHAT_ID=123456789
```

#### Generating `APP_ADMIN_PASSWORD_HASH`

The hash must be BCrypt. Generate it with any of:

```bash
# Using htpasswd (Apache utils)
htpasswd -bnBC 10 "" yourpassword | tr -d ':\n'

# Using Python (if available)
python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt(10)).decode())"
```

### 3. Run the API

```bash
cd app && mvn spring-boot:run
```

The API will be available at `http://localhost:8080`.

Flyway runs automatically on startup and applies all migrations in `app/src/main/resources/db/migration/`.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DB_URL` | Yes | — | JDBC URL for PostgreSQL. Example: `jdbc:postgresql://localhost:5432/finances` |
| `DB_USERNAME` | Yes | — | Database username |
| `DB_PASSWORD` | Yes | — | Database password |
| `JWT_SECRET` | Yes | — | Base64-encoded HS256 signing key (minimum 32 bytes). Generate with `openssl rand -base64 32` |
| `APP_ADMIN_EMAIL` | Yes | — | Email used to log in via `POST /api/auth/login` |
| `APP_ADMIN_PASSWORD_HASH` | Yes | — | BCrypt hash of the admin password |
| `OPENROUTER_API_KEY` | Yes | — | API key for OpenRouter (LLM calls) |
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram bot token from BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | Yes | — | Secret string sent by Telegram in `X-Telegram-Bot-Api-Secret-Token` |
| `TELEGRAM_ALLOWED_CHAT_ID` | Yes | — | Telegram chat ID authorised to interact with the bot |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of allowed CORS origins |

---

## Running tests

Integration tests use Testcontainers and spin up a real PostgreSQL container — Docker must be running.

```bash
# All tests (unit + integration + architecture)
cd app && mvn verify

# Unit tests only (no Docker required)
cd app && mvn test
```

JaCoCo coverage report is generated at `app/target/site/jacoco/index.html` after `mvn verify`.

---

## API reference

All routes except `/api/auth/**` and `/webhook` require `Authorization: Bearer <token>`.

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Returns a JWT valid for 7 days |

**Request body:**
```json
{ "email": "admin@example.com", "password": "yourpassword" }
```

**Response:**
```json
{ "token": "<jwt>", "expires_in": 604800 }
```

### Transactions

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/transactions` | List transactions (paginated) |
| `POST` | `/api/v1/transactions` | Create a transaction |
| `GET` | `/api/v1/transactions/{id}` | Get a transaction by ID |
| `PUT` | `/api/v1/transactions/{id}` | Update a transaction |
| `DELETE` | `/api/v1/transactions/{id}` | Delete a transaction |

### Categories

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/categories` | List active categories |
| `POST` | `/api/v1/categories` | Create a category |
| `PATCH` | `/api/v1/categories/{id}` | Update name or active status |
| `DELETE` | `/api/v1/categories/{id}` | Deactivate a category |

### Reports and export

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/reports/summary?start=&end=` | Totals per category for a period |
| `GET` | `/api/v1/reports/monthly?year=` | Monthly breakdown by category for a full year |
| `GET` | `/api/v1/export/csv?start=&end=` | Download expenses as CSV (UTF-8 BOM) |

### Telegram webhook

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhook` | Receives Telegram updates (validated via `X-Telegram-Bot-Api-Secret-Token`) |

---

## Documentation

Full documentation lives in [`personal-finances-doc/`](../personal-finances-doc/):

- [Architecture](../personal-finances-doc/content/architecture/) — system design, hexagonal layers, request flows
- [API Reference](../personal-finances-doc/content/api-reference/) — REST endpoints, authentication, error codes
- [Security](../personal-finances-doc/content/security/) — auth model, webhook validation, access control
- [Roadmap](../personal-finances-doc/content/roadmap/) — milestones and future plans
