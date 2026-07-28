"""
services/transaction_normalizer_service.py — Maps raw values into standard transaction formats.

Appends category normalization mappings and enforces default metadata labels.
"""
from datetime import datetime, date


class TransactionNormalizerService:
    @staticmethod
    def normalize_row_data(row: dict) -> dict:
        """
        Normalize columns of a parsed CSV row into target database models structure.
        """
        # Trim and normalize category casing (Title Case)
        category = row.get("category", "Uncategorized").strip().title()
        
        # Convert occurred_on back to a Date object if string
        occurred_on_val = row.get("occurred_on")
        if isinstance(occurred_on_val, str):
            occurred_on = datetime.strptime(occurred_on_val, "%Y-%m-%d").date()
        elif isinstance(occurred_on_val, date):
            occurred_on = occurred_on_val
        else:
            occurred_on = date.today()
            
        note = row.get("note")
        if note:
            note = note.strip()
            
        return {
            "occurred_on": occurred_on,
            "amount": float(row.get("amount", 0.0)),
            "type": row.get("type", "expense").strip().lower(),
            "category": category,
            "note": note,
            "source": "csv_import"
        }
