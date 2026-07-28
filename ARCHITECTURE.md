# FinSarthi Architecture & API Contracts (Phase 0)

This document is the authoritative architecture design and contracts freeze for the FinSarthi backend. All subsequent implementation phases must adhere strictly to these schemas, endpoint definitions, routing boundaries, and security/logging rules.

---

## 1. System Overview & Scope Boundaries

FinSarthi is a personal AI financial workspace powered by a multi-agent system. To maintain a focus on core features, functionality is split into an active V1 implementation and several stubbed domains.

### Agent Scope (V1)
- **Active Agents (V1-real):**
  - **Guardian (Fraud & Safety):** Watches for scams, suspicious links, and payment request validation.
  - **Learn (Financial Literacy):** Explains concepts in clear, user-preferred languages.
- **Inactive Agents (V1-stubbed/deferred):**
  - **Planner (Budget & Goals):** Locked/Unavailable in V1 (returns stubbed response).
  - **Coach (Habits & Behavior):** Locked/Unavailable in V1 (returns stubbed response).
  - **Navigator (Schemes & Benefits):** Locked/Unavailable in V1 (returns stubbed response).

---

## 2. Database Schema Design (11 Tables)

All tables use PostgreSQL database types. Every model must define corresponding Pydantic schemas for serialization and request validation.

```mermaid
erDiagram
    users ||--o{ refresh_tokens : owns
    users ||--|| digital_twins : profile
    users ||--|| user_preferences : preferences
    users ||--o{ conversations : starts
    users ||--o{ goals : sets
    users ||--o{ audit_logs : performs
    conversations ||--o{ messages : contains
    conversations ||--o{ agent_runs : triggers
    agent_runs ||--o{ agent_logs : generates
```

### 2.1. `users`
Tracks user account credentials and registration data.
*   **Service & Repository Owner:** `AuthService` / `UserRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Constraints & Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | `gen_random_uuid()` | Primary Key |
    | `name` | `TEXT` | Yes | — | User's display name |
    | `email` | `TEXT` | No | — | Case-insensitive UNIQUE index |
    | `password_hash` | `TEXT` | No | — | Hashed credentials |
    | `created_at` | `TIMESTAMPTZ` | No | `now()` | Timestamp |
    | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Timestamp |
*   **Indexes:**
    *   `idx_users_email` (Unique, btree on `lower(email)`)

### 2.2. `refresh_tokens`
Stores cryptographically secure, hashed refresh tokens to manage active authentication sessions.
*   **Service & Repository Owner:** `AuthService` / `RefreshTokenRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `user_id` | `UUID` | No | — | Foreign Key -> `users.id` (ON DELETE CASCADE) |
    | `token_hash` | `TEXT` | No | — | Token lookup value (SHA-256 hashed) |
    | `expires_at` | `TIMESTAMPTZ` | No | — | Expiration timestamp |
    | `revoked` | `BOOLEAN` | No | `false` | Active/Revocation status flag |
*   **Indexes:**
    *   `idx_refresh_tokens_token_hash` (Unique, btree)
    *   `idx_refresh_tokens_user_id` (btree)

### 2.3. `digital_twins`
The financial personalization profile representing the AI's understanding of the user's financial setup.
*   **Service & Repository Owner:** `ProfileService` / `DigitalTwinRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `user_id` | `UUID` | No | — | Foreign Key -> `users.id` (ON DELETE CASCADE), Unique |
    | `financial_goals` | `JSONB` | Yes | — | Flexible JSON representation of user goals |
    | `income_pattern` | `TEXT` | Yes | — | Qualitative description of income |
    | `risk_appetite` | `TEXT` | Yes | — | Profile classification (e.g. conserv, mod, aggressive) |
    | `literacy_level` | `TEXT` | Yes | — | Financial literacy level |
    | `language_preference` | `TEXT` | Yes | — | Preferred language for agent interactions |
    | `accessibility_needs` | `JSONB` | No | `'{}'::jsonb` | Vision/motion preference values (Pydantic-enforced) |
    | `behavioral_notes` | `JSONB` | Yes | — | Flexible unvalidated JSON of user habits |
    | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Update tracker |
*   **Indexes:**
    *   `idx_digital_twins_user_id` (Unique, btree)
    *   `idx_digital_twins_accessibility_needs` (gin)

### 2.4. `user_preferences`
UI settings and alert switches. Storing preferences here instead of overloading `digital_twins` preserves the distinct domain boundary between UI/behavioral settings and core financial personalization profiles.
*   **Service & Repository Owner:** `ProfileService` / `UserPreferenceRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `user_id` | `UUID` | No | — | Foreign Key -> `users.id` (ON DELETE CASCADE), Unique |
    | `theme` | `TEXT` | No | `'light'` | Theme name (`'light'`, `'dark'`, `'system'`) |
    | `notifications_enabled` | `BOOLEAN` | No | `true` | Master notifications switch |
    | `updated_at` | `TIMESTAMPTZ` | No | `now()` | Update tracker |
*   **Indexes:**
    *   `idx_user_preferences_user_id` (Unique, btree)

### 2.5. `conversations`
Represents an ongoing chat thread between the user and the agent team.
*   **Service & Repository Owner:** `ChatService` / `ConversationRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `user_id` | `UUID` | No | — | Foreign Key -> `users.id` (ON DELETE CASCADE) |
    | `title` | `TEXT` | Yes | — | Thread title |
    | `created_at` | `TIMESTAMPTZ` | No | `now()` | Time of conversation start |
*   **Indexes:**
    *   `idx_conversations_user_id` (btree)
    *   `idx_conversations_created_at` (btree, indexed for recency sorts)

### 2.6. `messages`
Individual dialog entries inside conversation threads.
*   **Service & Repository Owner:** `ChatService` / `MessageRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `conversation_id` | `UUID` | No | — | Foreign Key -> `conversations.id` (ON DELETE CASCADE) |
    | `role` | `TEXT` | No | — | Message sender type (`'user'` \| `'assistant'`) |
    | `content` | `TEXT` | No | — | Textual message contents |
    | `created_at` | `TIMESTAMPTZ` | No | `now()` | Message timestamp |
*   **Indexes:**
    *   `idx_messages_conversation_id` (btree)
    *   `idx_messages_created_at` (btree, indexed for temporal sorting)

### 2.7. `agent_runs`
Tracks live orchestration progress and agent status during asynchronous execution. Visited by the live UI.
*   **Service & Repository Owner:** `SupervisorService` (Orchestration) / `AgentRunRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `conversation_id` | `UUID` | No | — | Foreign Key -> `conversations.id` (ON DELETE CASCADE) |
    | `agent_name` | `TEXT` | No | — | Agent identifier |
    | `status` | `TEXT` | No | — | Current state (`'queued'`, `'running'`, `'completed'`, `'failed'`) |
    | `started_at` | `TIMESTAMPTZ` | No | — | Run start timestamp |
    | `completed_at` | `TIMESTAMPTZ` | Yes | — | Run end timestamp |
*   **Indexes:**
    *   `idx_agent_runs_conversation_id` (btree)

### 2.8. `agent_logs`
Granular developer execution and trace logs for offline debugging/auditing. Keeping this separate from `agent_runs` ensures the live status queries remain small and high-performance.
*   **Service & Repository Owner:** `SupervisorService` / `AgentLogRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `agent_run_id` | `UUID` | No | — | Foreign Key -> `agent_runs.id` (ON DELETE CASCADE) |
    | `event_type` | `TEXT` | No | — | Type of execution event |
    | `detail` | `JSONB` | Yes | — | Parameters and contexts. NEVER log secrets/PII |
    | `created_at` | `TIMESTAMPTZ` | No | `now()` | Timestamp |
*   **Indexes:**
    *   `idx_agent_logs_agent_run_id` (btree)
    *   `idx_agent_logs_created_at` (btree)

### 2.9. `goals`
Financial goals defined and monitored by the user.
*   **Service & Repository Owner:** `ProfileService` / `GoalRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `user_id` | `UUID` | No | — | Foreign Key -> `users.id` (ON DELETE CASCADE) |
    | `goal_name` | `TEXT` | No | — | Target goal name |
    | `target_amount` | `NUMERIC(14,2)` | No | — | Exact money amount needed |
    | `current_amount` | `NUMERIC(14,2)` | No | `0` | Savings amount achieved |
    | `deadline` | `DATE` | Yes | — | Deadline date |
    | `status` | `TEXT` | No | `'active'` | Status flag (`'active'`, `'completed'`, `'paused'`) |
*   **Indexes:**
    *   `idx_goals_user_id` (btree)

### 2.10. `knowledge_sources`
Tracks raw text vector ingestion metadata within ChromaDB. Supports Knowledge Hub attribution.
*   **Service & Repository Owner:** `KnowledgeService` / `KnowledgeSourceRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `source_name` | `TEXT` | No | — | Document title/name |
    | `category` | `TEXT` | Yes | — | Document category classification |
    | `ingested_at` | `TIMESTAMPTZ` | No | `now()` | Timestamp of document parsing |
    | `active` | `BOOLEAN` | No | `true` | Active vector availability indicator |

### 2.11. `audit_logs`
Mandatory tracking for modifications of sensitive data. Writes occur synchronously on mutations to profiles, goals, and user preferences.
*   **Service & Repository Owner:** `ProfileService` (Global context wrapper) / `AuditLogRepository`
*   **Columns:**
    | Column | Type | Nullable | Default | Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `id` | `UUID` | No | — | Primary Key |
    | `user_id` | `UUID` | No | — | Foreign Key -> `users.id` (ON DELETE CASCADE) |
    | `action` | `TEXT` | No | — | Action identifier (e.g. `'profile_updated'`, `'goal_created'`) |
    | `before` | `JSONB` | Yes | — | Row data prior to changes |
    | `after` | `JSONB` | Yes | — | Row data post changes |
    | `created_at` | `TIMESTAMPTZ` | No | `now()` | Log write timestamp |
*   **Indexes:**
    *   `idx_audit_logs_user_id` (btree)
    *   `idx_audit_logs_created_at` (btree)

---

## 2.12. Key Database Constraints & Design Rules

To ensure performance, data integrity, and compliance across future development phases, the following database design rules must be implemented strictly in Phase 4:

1.  **Cascading User Deletes:** Deleting a user must cascade and automatically delete the user's `refresh_tokens`, `digital_twins`, `user_preferences`, `conversations`, `goals`, and `audit_logs` (`ON DELETE CASCADE`). This ensures complete deletion compliance (Right to Deletion) and guarantees no orphaned rows remain.
2.  **Cascading Chat Deletes:** Deleting a conversation must cascade and delete all associated `messages` and `agent_runs`.
3.  **Cascading Agent Log Deletes:** Deleting an agent run must cascade and delete its associated execution traces (`agent_logs`).
4.  **No-Delete Security Policy for Audit Logs:** The `audit_logs` table represents a non-repudiation audit trail. There must be no code paths in the repositories, services, or endpoints that allow rows from this table to be updated or deleted. Enforced append-only.
5.  **Pydantic-Only JSON Schema Constraints:** To maintain flexible schemas, JSON columns (such as `accessibility_needs` or `financial_goals`) must be typed as standard `JSONB` columns in PostgreSQL without database-level `CHECK` constraints. Structural schema enforcement must be performed strictly at the Pydantic validator layer inside the application logic.
6.  **Agent Log Safety:** Developers must configure agents in Phase 9 to never write user passwords, secret keys, or authentication tokens into the `agent_logs.detail` field.
7.  **1 Repository Per Table:** To maintain clear architectural boundaries, each of the 11 tables must be managed by its own unique repository (e.g., `agent_logs` has `AgentLogRepository`, and is never queried through `agent_runs`).

---

## 3. API Endpoints Surface Matrix

The API layer is versioned. Endpoints marked as `V1-real` are fully backed by services and repositories. Endpoints marked as `V1-stubbed` return the frozen unavailable format payload.

| Method | Endpoint | Target V1 Status | Description / Behavior |
| :--- | :--- | :--- | :--- |
| **POST** | `/auth/register` | `V1-real` | Create a new user account, initialize preferences & digital twin |
| **POST** | `/auth/login` | `V1-real` | Authenticate credentials, return access token and refresh token |
| **POST** | `/auth/refresh` | `V1-real` | Re-issue access tokens using valid, unrevoked refresh tokens |
| **POST** | `/auth/logout` | `V1-real` | Revoke user refresh token immediately |
| **POST** | `/auth/forgot-password` | `V1-stubbed` | Request password reset code (returns stubbed response) |
| **POST** | `/auth/verify-otp` | `V1-stubbed` | Verify OTP code for password reset (returns stubbed response) |
| **POST** | `/chat/conversations` | `V1-real` | Initialize a new conversation thread |
| **GET** | `/chat/conversations` | `V1-real` | Fetch conversation list (newest first, supports search/paging) |
| **POST** | `/chat/conversations/{id}/messages` | `V1-real` | Post a user message. Streams back assistant response via SSE |
| **GET** | `/agents/status` | `V1-real` | Merges static agent registry with live dynamic `agent_runs` statuses |
| **GET** | `/knowledge/search` | `V1-real` | Query matching vector embeddings via ChromaDB and return sources |
| **GET** | `/knowledge/categories` | `V1-real` | Fetch matching ingestion categories list |
| **GET** | `/goals` | `V1-real` | List current user goals. Returns empty array if none exist |
| **POST** | `/goals` | `V1-real` | Create a new financial goal (validates schemas) |
| **GET** | `/insights/summary` | `V1-stubbed` | Retrieve financial summary and metrics (returns stubbed response) |
| **GET** | `/profile` | `V1-real` | Get user profile fields, preferences, and Twin settings |
| **PATCH** | `/profile` | `V1-real` | Update user metadata, updates preferences table |
| **GET** | `/profile/accessibility` | `V1-real` | Fetch accessibility needs from Digital Twin profile |
| **PATCH** | `/profile/accessibility` | `V1-real` | Update accessibility needs inside `digital_twins` |
| **GET** | `/search` | `V1-real` | Global search returning matches from conversations & knowledge only |

---

## 4. Shared Response Contracts

### 4.1. Frozen "Unavailable Feature" Response Shape
All endpoints tagged as `V1-stubbed` (or logic handling deferred features) must return the following JSON structure. This is declared globally as `UnavailableResponse` in `schemas/common.py`:

```json
{
  "available": false,
  "message": "This feature is not available in V1.",
  "data": null
}
```

### 4.2. Global Standard Error Response Shape
All unhandled server errors (500) and client errors (400, 422, etc.) must return a uniform error object representation. Internal details must never be exposed:

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later."
  }
}
```

---

## 5. Architectural Layering & Domain Boundaries

To guarantee clean maintainability, the backend imposes strict boundaries between the HTTP, Business Logic, and Database Access layers.

```
+-------------------------------------------------------------+
|                        FastAPI Router                       |
|   (Validates HTTP requests via Pydantic; checks permissions) |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                        Service Layer                        |
|   (AuthService, ChatService, ProfileService, etc.)          |
|   * Zero HTTP logic (no request, header, response objects)   |
|   * Holds transaction boundaries & orchestrates repository   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                      Repository Layer                       |
|   (UserRepository, MessageRepository, etc.)                |
|   * Single model scope (no cross-boundary dependencies)      |
|   * Pure database operations; zero business validation       |
+-------------------------------------------------------------+
```

### 5.1. Domain Service Boundaries
Services operate on a single domain. They must never cross domain scopes in a single service block. If cross-domain actions are required, they must be coordinated by a controller, router, or dedicated orchestrator (e.g. `SupervisorService` coordinating `ChatService` and agents).
- **AuthService:** Handles token issuance, revocation, and authentication checks.
- **ChatService:** Handles conversation creation, messaging databases, and history queries.
- **SupervisorService:** Orchestrates agent execution runs and coordinates the RAG ingestion loop.
- **ProfileService:** Controls updates to profile metadata, preferences, goals, and twins.

### 5.2. Repository Boundaries
- Exactly **one repository per database model**.
- Repositories must never contain business rules. They only carry raw database instructions (SQL / ORM operations).

### 5.3. Middleware Rules
- Security context extraction (JWT verification) is handled uniformly via dependency injection middleware.
- Rate-limiting (using Redis) wraps all authentication endpoints (`/auth/login`, `/auth/register`). No exceptions are permitted.

---

## 6. Environment Variables Reference

A `.env` template schema that all developers must provide locally. Plaintext values must **never** be committed.

| Variable Name | Type | Recommended Value (Local) | Purpose |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | `postgresql+asyncpg://postgres:postgres@localhost:5432/finsarthi` | SQLAlchemy database link |
| `REDIS_URL` | String | `redis://localhost:6379/0` | Rate limiting and caching store |
| `CHROMA_HOST` | String | `localhost` | Vectordb instance host |
| `CHROMA_PORT` | Integer | `8000` | Vectordb instance port |
| `JWT_SECRET_KEY` | String | *[Secure Generated Key]* | Secret key for signing JWTs |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `15` | Expiry duration for API tokens |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Integer | `7` | Expiry duration for refresh tokens |
| `LLM_PROVIDER` | String | `gemini` | LLM target: `gemini` \| `openai` \| `claude` \| `ollama` |
| `LLM_API_KEY` | String | *[API Key]* | Key for accessing external LLM API |
| `CORS_ALLOWED_ORIGINS` | String | `["http://localhost:5173", "http://localhost:3000"]` | Allowed frontends |
| `RATE_LIMIT_LOGIN_ATTEMPTS` | Integer | `5` | Allowable attempts |
| `RATE_LIMIT_WINDOW_MINUTES` | Integer | `15` | Rate limiting time window size |
| `ENVIRONMENT` | String | `dev` | Server environment: `dev` \| `test` \| `prod` |

---

## 7. Security, Validation & Logging Rules

### 7.1. Validation
- Every request payload must be explicitly validated against a dedicated Pydantic input schema at the router boundary.
- Every response must match a declared output schema. Even stubbed routes must validate against `UnavailableResponse`.

### 7.2. Security
- **Hashing:** User passwords must be hashed using `bcrypt` (minimum rounds: 12). Refresh tokens must be SHA-256 hashed before storage (raw keys are never saved).
- **Exceptions:** No raw exception logs or stack traces may be returned to the client. Uncaught exceptions map automatically to the structured HTTP 500 JSON schema.
- **Audit Trails:** Mutations of tables `digital_twins`, `goals`, or `user_preferences` must trigger a synchronous write to `audit_logs` capturing user details and pre/post values.

### 7.3. Logging Strategy
- Logs must follow structured JSON format.
- A unique correlation `Request-ID` must be generated for each request and attached to all downstream logs.
- **Strict Data Redaction:** Raw user passwords, raw JWTs, refresh tokens, and API secret keys must be automatically filtered/redacted from all logs. Log only truncated hashes or anonymized identifiers where tracking is necessary.

---

## 8. Design Principles (Incremental Architecture)

FinSarthi follows a strictly incremental architecture strategy. Features are activated only after their required domain models and infrastructure exist. 

This prevents fabricated functionality, keeps the UI and implementation truthful, and allows each capability to evolve independently.

- **Data-Driven Agents:** `Planner` requires actual transactions to analyze. `Coach` requires behavioral history. `Navigator` requires user profile enrichment.
- **Infrastructure-Driven Processing:** Background workers and asynchronous agent execution require mature infrastructure (e.g., Redis Queues, Event Buses).
- **No Faking It:** If a feature lacks the required data or infrastructure, its UI must honestly reflect a "Waiting" or "Planned" state instead of displaying placeholder metrics.

---

## 9. Future Architecture (Post-V1 Roadmap)

The long-term vision for FinSarthi is to evolve into a fully autonomous multi-agent system. This section is strictly documentation for future phases and does not reflect current V1 capabilities.

### Phase Sequence

#### V1 (Current)
- Authentication
- Chat
- Guardian (Conversation-driven)
- Learn (Conversation-driven)
- Dashboard

#### V2
Introduce the core financial domain:
- New Entities: Transactions, Accounts, Budgets, Expense Categories, Savings.
- Agents: `Planner` and `Coach` become request-driven services using real transaction data.
- Note: No background workers yet. Agents run synchronously on request.

#### V3
Introduce asynchronous infrastructure:
- Infrastructure: Redis Queue, Background Jobs, Event Bus, Scheduled Workers.
- Example Events: `TransactionCreated`, `BudgetUpdated`, `GoalCompleted`, `ProfileUpdated`, `PaymentScanned`.

#### V4
Autonomous Multi-Agent System:
- Architecture: `Event` -> `Worker` -> `Agents (Planner/Coach/Guardian/Navigator/Learn)` -> `Store Insight` -> `Dashboard`.
- Agents operate autonomously in the background, rather than only during chat conversations or dashboard loads.

### Future Database Changes (Documentation Only)
To support autonomous agents, the database schema will eventually expand to include:
- `transactions`
- `accounts`
- `budgets`
- `investment_portfolio`
- `agent_insights`

**Why:** Autonomous agents must store their insights independently from conversations. Conversation-driven AI and background-generated insights serve different purposes and require isolated storage layers (`agent_insights` vs `messages`).
