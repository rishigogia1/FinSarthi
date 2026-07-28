"""
services/csv_parser_service.py — Safely parses raw CSV text and validates formatting constraints.

Validates required headers: date, amount, type, category. Captures row-level errors gracefully.
"""
import csv
import io
from datetime import datetime
from app.core.config import settings


class CSVParserService:
    @staticmethod
    def parse_csv_data(csv_content: str) -> tuple[list[dict], list[dict]]:
        """
        Parse CSV string into a list of row dicts and errors list.
        Returns:
            (parsed_rows_list, error_reports_list)
        """
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        
        # Verify required headers
        if not reader.fieldnames:
            return [], [{"row": 0, "message": "CSV file is empty or missing headers."}]
            
        headers = [h.lower().strip() for h in reader.fieldnames]
        required = ["date", "amount", "type", "category"]
        missing = [req for req in required if req not in headers]
        if missing:
            return [], [{"row": 0, "message": f"Missing required headers: {', '.join(missing)}"}]
            
        parsed_rows = []
        errors = []
        
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count > settings.CSV_IMPORT_MAX_ROWS:
                errors.append({
                    "row": row_count,
                    "message": f"Maximum row limit exceeded ({settings.CSV_IMPORT_MAX_ROWS} rows allowed)."
                })
                break
                
            # Normalize headers case for dictionary access
            normalized_row = {k.lower().strip(): v for k, v in row.items() if k}
            
            row_errors = []
            
            # 1. Parse Date
            dt_str = normalized_row.get("date", "").strip()
            occurred_on = None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    occurred_on = datetime.strptime(dt_str, fmt).date()
                    break
                except ValueError:
                    continue
            if not occurred_on:
                row_errors.append(f"Invalid date format '{dt_str}'. Supported: YYYY-MM-DD, DD-MM-YYYY, MM/DD/YYYY.")
                
            # 2. Parse Amount
            amt_str = normalized_row.get("amount", "").strip()
            amount = 0.0
            try:
                amount = float(amt_str)
                if amount <= 0:
                    row_errors.append("Amount must be a positive number.")
            except ValueError:
                row_errors.append(f"Invalid amount value '{amt_str}'. Must be a float.")
                
            # 3. Parse Type
            tx_type = normalized_row.get("type", "").strip().lower()
            if tx_type not in ("income", "expense"):
                row_errors.append(f"Invalid transaction type '{tx_type}'. Must be 'income' or 'expense'.")
                
            # 4. Parse Category
            category = normalized_row.get("category", "").strip()
            if not category:
                row_errors.append("Category cannot be blank.")
                
            note = normalized_row.get("note", "")
            if note:
                note = note.strip()
                if len(note) > 500:
                    row_errors.append("Note length cannot exceed 500 characters.")
            else:
                note = None
                
            if row_errors:
                errors.append({
                    "row": row_count,
                    "message": "; ".join(row_errors)
                })
            else:
                parsed_rows.append({
                    "row_index": row_count,
                    "occurred_on": str(occurred_on),
                    "amount": amount,
                    "type": tx_type,
                    "category": category,
                    "note": note
                })
                
        return parsed_rows, errors
