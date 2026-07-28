"""
services/deduplication_service.py — Duplicate detection using fingerprints comparisons.

Flags batch collisions and matches against existing database transaction entries.
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.transaction_repository import TransactionRepository


class DeduplicationService:
    @staticmethod
    def generate_fingerprint(user_id: str, occurred_on: date, amount: float, tx_type: str, category: str) -> str:
        """Construct a deterministic unique string identifier for comparison checks."""
        # Normalize fields for matching (e.g. casing and precision rounding)
        cat_norm = category.strip().lower()
        type_norm = tx_type.strip().lower()
        amt_norm = round(float(amount), 2)
        return f"{user_id}:{occurred_on}:{amt_norm}:{type_norm}:{cat_norm}"

    @staticmethod
    async def flag_duplicates(
        session: AsyncSession,
        user_id: str,
        parsed_rows: list[dict]
    ) -> list[dict]:
        """
        Scan parsed CSV rows and flag matching records as duplicates.
        Returns:
            list of dicts containing row details and duplicate statuses.
        """
        # Fetch existing database transactions for the user
        existing_txs = await TransactionRepository.list_user_transactions(session, user_id)
        
        # Build set of existing fingerprints
        existing_fingerprints = set()
        for tx in existing_txs:
            fp = DeduplicationService.generate_fingerprint(
                user_id=user_id,
                occurred_on=tx.occurred_on,
                amount=float(tx.amount),
                tx_type=tx.type,
                category=tx.category
            )
            existing_fingerprints.add(fp)
            
        results = []
        batch_fingerprints = set()
        
        for row in parsed_rows:
            # Convert occurred_on to date for formatting checks
            from datetime import datetime
            if isinstance(row["occurred_on"], str):
                occurred_on = datetime.strptime(row["occurred_on"], "%Y-%m-%d").date()
            else:
                occurred_on = row["occurred_on"]
                
            fp = DeduplicationService.generate_fingerprint(
                user_id=user_id,
                occurred_on=occurred_on,
                amount=row["amount"],
                tx_type=row["type"],
                category=row["category"]
            )
            
            status = "accepted"
            errors = []
            
            # Check database match
            if fp in existing_fingerprints:
                status = "duplicate"
                errors.append("Matches an existing transaction in your history.")
            # Check batch duplicate match
            elif fp in batch_fingerprints:
                status = "duplicate"
                errors.append("Duplicate entry found within the same import file.")
            else:
                batch_fingerprints.add(fp)
                
            results.append({
                "row_index": row["row_index"],
                "status": status,
                "errors": errors if errors else None,
                "normalized_row": {
                    "occurred_on": str(occurred_on),
                    "amount": row["amount"],
                    "type": row["type"],
                    "category": row["category"],
                    "note": row["note"]
                }
            })
            
        return results
