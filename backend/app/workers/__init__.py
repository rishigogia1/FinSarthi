"""app/workers/ — Lightweight post-response background task modules.

NOTE: These are NOT durable job workers. They run in-process via FastAPI
BackgroundTasks after the HTTP response has been sent. If the process crashes
mid-execution, the work is lost. For durability, recovery after restart, or
scheduled execution, a queue-backed worker system (Celery, Arq, etc.) would
be needed — that is future scope beyond V1.
"""
