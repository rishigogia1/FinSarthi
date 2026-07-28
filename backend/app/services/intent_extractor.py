"""
services/intent_extractor.py — LLM & pattern-based intent extractor for financial commands.
"""
import re
import json
import logging
from datetime import date
from app.schemas.planner import ParsedIntentSchema
from app.models.transaction import BUILTIN_CATEGORIES
from app.services.llm_service import LLMService, LLMError

logger = logging.getLogger("app.services.intent_extractor")

# Semantic Category Dictionary
CATEGORY_KEYWORD_MAP = {
    "Food": [
        "food", "coffee", "tea", "chai", "espresso", "latte", "cappuccino", "cafe", "starbucks",
        "breakfast", "lunch", "dinner", "meal", "snack", "pizza", "burger", "restaurant",
        "groceries", "grocery", "swiggy", "zomato", "blinkit", "zepto", "instamart", "bakery",
        "supermarket", "kitchen"
    ],
    "Transport": [
        "uber", "ola", "rapido", "cab", "taxi", "auto", "rickshaw", "petrol", "diesel", "fuel",
        "bus", "train", "metro", "flight", "airline", "parking", "toll", "mechanic", "transport",
        "commute", "travel ticket"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "shirt", "t-shirt", "pants", "jeans",
        "dress", "clothes", "clothing", "shoes", "sneakers", "electronics", "laptop", "mobile",
        "phone", "gadget", "shopping", "apparel", "store"
    ],
    "Bills": [
        "rent", "electricity", "power", "water", "gas", "cylinder", "wifi", "internet",
        "broadband", "mobile bill", "recharge", "maintenance", "bill", "utility"
    ],
    "Entertainment": [
        "movie", "cinema", "netflix", "spotify", "hotstar", "prime", "game", "gaming",
        "concert", "event", "show", "theatre", "entertainment", "outing", "pub", "bar"
    ],
    "Healthcare": [
        "doctor", "hospital", "clinic", "medicine", "pharmacy", "lab", "blood test",
        "health", "dentist", "checkup", "medical"
    ],
    "Education": [
        "school", "college", "tuition", "course", "udemy", "coursera", "books", "exam fee",
        "fee", "education", "class"
    ],
    "Travel": [
        "hotel", "resort", "airbnb", "trip", "vacation", "tour", "sightseeing"
    ],
    "Salary": [
        "salary", "stipend", "paycheck", "bonus", "dividend", "payout"
    ],
    "Investment": [
        "sip", "mutual fund", "stock", "share", "zerodha", "groww", "crypto", "bitcoin", "gold", "investment"
    ]
}


class IntentExtractor:
    @classmethod
    async def extract(cls, user_message: str) -> ParsedIntentSchema:
        """
        Parses user message to identify financial intents (add_expense, add_income, query_planner).
        Uses deterministic regex rules & semantic mapping first, falling back to LLM JSON extraction.
        """
        text = user_message.strip()
        lower = text.lower()

        # 1. Regex & Semantic Category Extraction
        regex_result = cls._try_regex_extraction(text, lower)
        if regex_result:
            logger.info("Intent extracted via regex & semantic rule: %s (cat=%s, confidence=%.2f)", regex_result.intent, regex_result.category, regex_result.confidence)
            return regex_result

        # 2. LLM fallback extraction for complex/natural phrasing
        try:
            llm_result = await cls._try_llm_extraction(text)
            if llm_result:
                logger.info("Intent extracted via LLM: %s (cat=%s, confidence=%.2f)", llm_result.intent, llm_result.category, llm_result.confidence)
                return llm_result
        except Exception as e:
            logger.warning("LLM intent extraction fallback encountered error: %s", e)

        # 3. Default fallback to general chat
        return ParsedIntentSchema(
            intent="general_chat",
            confidence=1.0,
            requires_confirmation=False
        )

    @classmethod
    def _try_regex_extraction(cls, text: str, lower: str) -> ParsedIntentSchema | None:
        # Check Guardian (Fraud & Security)
        if any(kw in lower for kw in ["is this link safe", "is this qr code safe", "suspicious link", "phishing", "scam", "upi fraud", "verify payment link", "fake investment", "help protect me from financial scams"]):
            return ParsedIntentSchema(
                intent="query_guardian",
                confidence=0.95,
                requires_confirmation=False
            )

        # Check Learn (Financial Education)
        if any(kw in lower for kw in ["explain sip", "what is sip", "explain mutual fund", "what is mutual fund", "what is inflation", "emergency fund definition", "explain tax regime", "teach me essential personal finance"]):
            return ParsedIntentSchema(
                intent="query_learn",
                confidence=0.95,
                requires_confirmation=False
            )

        # Check Navigator (Affordability, Schemes & Goal Planning)
        if any(kw in lower for kw in ["can i afford", "should i buy", "how long to save", "how much to save monthly", "recommend relevant government", "government schemes"]):
            return ParsedIntentSchema(
                intent="query_navigator",
                confidence=0.95,
                requires_confirmation=False
            )

        # Check query coach intents
        if any(kw in lower for kw in ["am i overspending", "am i spending too much", "overspending check", "am i spending wisely", "analyse my spending", "identify where i can realistically save"]):
            return ParsedIntentSchema(
                intent="query_coach_overspending",
                confidence=0.95,
                requires_confirmation=False
            )
        if any(kw in lower for kw in ["how are my spending habits", "spending habits", "what are my habits", "my habit score", "coach score", "how is my spending pattern"]):
            return ParsedIntentSchema(
                intent="query_coach_habits",
                confidence=0.95,
                requires_confirmation=False
            )

        # Check query planner
        if any(kw in lower for kw in ["how much have i spent", "where is my money going", "my spending summary", "planner summary", "my monthly expenses", "show my budget", "my cashflow", "analyse my expenses", "analyze my expenses"]):
            return ParsedIntentSchema(
                intent="query_planner",
                confidence=0.95,
                requires_confirmation=False
            )

        # Currency & transaction extraction rule: Must have spending verb + numerical amount
        amount_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d{1,2})?)\s*(?:rupees|rs|inr)?', text, re.IGNORECASE)
        
        # Explicit expense verbs
        expense_verbs = ["spent", "paid", "bought", "debited", "purchased", "recharged"]
        # Explicit income verbs
        income_verbs = ["received", "credited", "salary", "freelance", "earned", "payout", "got paid"]

        has_expense_verb = any(verb in lower for verb in expense_verbs)
        has_income_verb = any(verb in lower for verb in income_verbs)

        if not (has_expense_verb or has_income_verb):
            return None

        amount = None
        if amount_match:
            try:
                raw_amt = amount_match.group(1).replace(",", "")
                val = float(raw_amt)
                if val > 0:
                    amount = val
            except ValueError:
                pass

        if not amount:
            # Only trigger if text explicitly says e.g. "I spent on coffee" without amount
            return ParsedIntentSchema(
                intent="add_expense" if has_expense_verb else "add_income",
                confidence=0.4,
                requires_confirmation=True,
                clarification_prompt="I noticed you mentioned a transaction. Could you specify the exact amount in ₹?"
            )

        # Semantic Category Normalization
        matched_cat = cls.normalize_category(lower)
        intent_name = "add_income" if has_income_verb else "add_expense"

        return ParsedIntentSchema(
            intent=intent_name,
            confidence=0.95,
            requires_confirmation=False,
            amount=amount,
            category=matched_cat,
            date=date.today(),
            description=text
        )

    @classmethod
    def normalize_category(cls, text_lower: str) -> str:
        """Maps user keywords semantically to built-in categories."""
        for category, keywords in CATEGORY_KEYWORD_MAP.items():
            for kw in keywords:
                if kw in text_lower:
                    return category
        return "Other"

    @classmethod
    async def _try_llm_extraction(cls, text: str) -> ParsedIntentSchema | None:
        system_prompt = (
            "You are a financial intent classifier. Classify the user message into JSON with these exact fields:\n"
            "{\n"
            '  "intent": "add_expense" | "add_income" | "query_planner" | "query_coach_habits" | "query_coach_overspending" | "query_guardian" | "query_learn" | "query_navigator" | "general_chat",\n'
            '  "confidence": float (0.0 to 1.0),\n'
            '  "requires_confirmation": boolean,\n'
            '  "amount": float or null,\n'
            '  "category": string or null (Choose semantically from: Food, Shopping, Transport, Bills, Utilities, Entertainment, Healthcare, Education, Travel, Salary, Investment, Other),\n'
            '  "description": string or null,\n'
            '  "clarification_prompt": string or null\n'
            "}\n"
            "Return ONLY raw valid JSON, no markdown tags."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        res = await LLMService.generate(messages=messages, temperature=0.1, max_tokens=150, timeout=4.0)
        raw_content = res["content"].strip()

        if raw_content.startswith("```"):
            raw_content = re.sub(r"^```[a-z]*\n?", "", raw_content, flags=re.IGNORECASE)
            raw_content = re.sub(r"\n?```$", "", raw_content)

        data = json.loads(raw_content)
        intent = data.get("intent", "general_chat")

        valid_intents = [
            "add_expense", "add_income", "query_planner", "query_coach_habits",
            "query_coach_overspending", "query_guardian", "query_learn", "query_navigator", "general_chat"
        ]
        if intent not in valid_intents:
            intent = "general_chat"

        cat = data.get("category")
        normalized_cat = cls.normalize_category(cat.lower()) if cat else "Other"

        return ParsedIntentSchema(
            intent=intent,
            confidence=float(data.get("confidence", 0.8)),
            requires_confirmation=bool(data.get("requires_confirmation", False)),
            amount=float(data["amount"]) if data.get("amount") else None,
            category=normalized_cat,
            date=date.today(),
            description=str(data.get("description")) if data.get("description") else text,
            clarification_prompt=str(data.get("clarification_prompt")) if data.get("clarification_prompt") else None
        )
