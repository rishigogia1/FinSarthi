# Architecture Overview

FinSarthi is built using the **Service-Repository-Model** pattern to keep business logic isolated, easily testable, and maintainable. This architecture separates concerns into distinct layers, allowing the application to scale elegantly.

## High-Level Modules

- **API Layer (`app/api`):** Exposes FastAPI endpoints grouped by domain (e.g., transactions, goals, admin). Routes handle HTTP validation, authentication checks, and direct the requests to the corresponding services.
- **Service Layer (`app/services`):** Contains the core business logic. Services coordinate between repositories, third-party APIs (like the mocked LLM layer), and background tasks.
- **Repository Layer (`app/repositories`):** Abstraction over the database. Repositories execute raw queries or ORM commands using SQLAlchemy, returning Pydantic models or dictionaries to the service layer.
- **Model Layer (`app/models` & `app/schemas`):** Defines the database structure via SQLAlchemy (`models`) and the data validation/serialization structures via Pydantic (`schemas`).

## Request Flow

1. **Client Request:** An HTTP request hits the FastAPI router.
2. **Middleware & Auth:** Global rate limiting middleware applies. Dependencies (`Depends`) extract and validate the JWT token to identify the current user and their roles.
3. **Endpoint Handler:** The router validates the request body against Pydantic schemas. It then instantiates the required service and calls a specific method.
4. **Service Execution:** The service contains the logic (e.g., validating budgets or generating insights). It may query the database via the Repository Layer.
5. **Database Interaction:** The Repository Layer issues SQLAlchemy queries to PostgreSQL.
6. **Response Generation:** The service returns domain objects to the router, which serializes them back to JSON using Pydantic and returns the HTTP response.
7. **Background Processing:** If async operations are needed (e.g., CSV imports, sending emails), FastAPI's `BackgroundTasks` are enqueued right before returning the response.

## Core Workflows

### Authentication
JWT tokens are issued upon login. The `AuthService` manages token generation and validation. Access to endpoints is secured by dependency injection, ensuring the caller is authenticated. Specific routes (e.g., `/admin`) have an additional dependency that asserts the user's `role`.

### Data Import & Deduplication
For CSV imports, users upload a file, which triggers a parsing process in the `import_service.py`. A "preview" payload is created. The user can review the preview, and upon confirmation, the preview is processed to write transactions to the database. Deduplication checks hash transaction details to avoid creating duplicates.

### AI Insights
Insights are generated deterministically first (e.g., computing a forecast based on moving averages), followed by an AI layer that "explains" the data. If the AI provider is down, the system falls back to safe template-based explanations, ensuring high availability.

### Demo & Admin Pieces
- **Admin Dashboard:** Endpoints restricted to `admin` role allow generating system-wide audit logs and CSV exports.
- **Demo Mode:** An isolated demo reset flow can safely tear down a user's mock data and re-seed it to create an impressive "out of the box" state for presentations.

## Deployment Architecture
The backend is containerized using Docker. `docker-compose.yml` orchestrates three primary services:
1. `backend`: The FastAPI application.
2. `db`: PostgreSQL instance holding the relational data.
3. `redis`: Redis instance used for rate-limiting, idempotency keys, and fast temporary caching.
