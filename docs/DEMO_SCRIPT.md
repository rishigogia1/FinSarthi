# FinSarthi Demo Script

This script outlines a 5-minute interactive walkthrough to demonstrate the core features of the FinSarthi backend, ideal for technical interviews or portfolio presentations.

## Preparation
1. Ensure the system is running via `docker-compose up`.
2. Ensure you have the `DEMO_MODE_ENABLED=true` flag set in your `.env` file.
3. Open the Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Step 1: The Clean Slate & Demo Reset (1 min)
*Goal: Show how easily the system can be seeded for a presentation without manual data entry.*

1. **Register a User:** Use `POST /api/auth/register` to create a new test user (e.g., `demo@example.com`).
2. **Login:** Use `POST /api/auth/login` to obtain the JWT token and authorize in the Swagger UI.
3. **Execute Reset:** Trigger `POST /api/demo/reset`.
   * **Narrative:** "Instead of manually creating transactions, budgets, and goals for this demo, I built a safe `/demo/reset` endpoint. It wipes the current user's state and deterministically seeds 6 months of financial history. Notice how it's protected by an environment flag so this can't happen in production."

## Step 2: Core Financials & Deduplication (1.5 min)
*Goal: Demonstrate robust API design and data integrity.*

1. **Fetch Transactions:** Hit `GET /api/transactions`.
   * **Narrative:** "Here are the seeded transactions. You can see pagination and filtering built in."
2. **Upload a Duplicate CSV:** Use `POST /api/sync/csv-preview` with a sample CSV that contains transactions already seeded.
   * **Narrative:** "When importing data, we use a preview-before-commit architecture. If I try to upload transactions that already exist, the backend calculates an idempotency hash and automatically flags them as duplicates, ensuring data integrity."

## Step 3: AI Insights with Fallbacks (1.5 min)
*Goal: Highlight the separation of deterministic calculation and AI presentation.*

1. **Trigger Forecast Insight:** Call `GET /api/insights/forecast`.
   * **Narrative:** "Here we see an AI-generated insight explaining next month's forecast. Crucially, the forecast numbers are computed deterministically in SQL/Python first. The LLM is only given the final numbers to 'explain' them."
2. **Explain the Fallback Strategy:**
   * **Narrative:** "If the AI provider (like OpenAI) goes down, the backend uses a resilient circuit-breaker pattern. It falls back to template-based responses. This guarantees that the user still gets their financial analytics even if the AI is unavailable."

## Step 4: Admin Controls & Export (1 min)
*Goal: Show role-based access control and export capabilities.*

1. **Attempt Admin Access:** As the standard user, try hitting `GET /api/admin/audit`. It will return a `403 Forbidden`.
   * **Narrative:** "Security is enforced at the route dependency layer. Standard users cannot access admin routes."
2. **Toggle Admin Role:** (Explain that in a real scenario you would update the DB or use a superadmin token, but for now, you can mention the role-based auth).
3. **Download CSV Export:** Call `GET /api/exports/transactions`.
   * **Narrative:** "For data portability, we use a CSV-first export strategy. This streams the data out efficiently and is immediately useful to the user, proving the system is ready for real-world application."

---
*End of Demo.*
