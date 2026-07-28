# FinSarthi Backend

FinSarthi is a personal AI financial workspace backend powered by a multi-agent system. It is built to be a robust, production-ready system to manage personal finances, generate insights, and automate financial tracking. 

## Features
- **User Authentication:** JWT-based login, registration, and session tracking.
- **Financial Core:** Manage transactions, goals, budgets, and recurring cashflows.
- **AI Insights:** Automated financial forecasting and behavioral insights (mocked LLM integrations).
- **Data Ingestion:** CSV import pipelines with preview-before-commit logic.
- **Admin Dashboard:** Role-based access to audit logs and exports.
- **Demo Mode:** An easy reset flow to demonstrate core functionality safely.

## Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (with Alembic for migrations and SQLAlchemy for ORM)
- **Caching & Rate Limiting:** Redis
- **Background Tasks:** FastAPI `BackgroundTasks`
- **Containerization:** Docker & Docker Compose

## Setup and Quickstart

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (if running locally without Docker)

### Running with Docker Compose
The easiest way to spin up the system is using Docker Compose. This will start the FastAPI backend, PostgreSQL, and Redis.

1. **Clone the repository.**
2. **Setup environment variables:**
   Copy the example environment file and fill in required values if necessary (defaults are provided for local testing).
   ```bash
   cp backend/.env.example backend/.env
   ```
3. **Run the services:**
   ```bash
   docker-compose up --build -d
   ```
4. **Access the API Documentation:**
   Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

## Documentation
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Overview](docs/API_OVERVIEW.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
