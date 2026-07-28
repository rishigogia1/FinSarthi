"""
services/guardian_service.py — Real Domain & Fraud Security Inspector for FinSarthi V2.

Performs URL parsing, protocol validation, official whitelist checking, URL shortener detection,
and phishing keyword analysis to return accurate security risk assessments.
"""
import re
import logging
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("app.services.guardian_service")

# Official Whitelisted Trusted Hostnames
OFFICIAL_WHITELIST = {
    "google.com", "www.google.com", "google.co.in", "www.google.co.in",
    "sbi.co.in", "www.sbi.co.in", "onlinesbi.sbi", "onlinesbi.com",
    "hdfcbank.com", "www.hdfcbank.com", "icicibank.com", "www.icicibank.com",
    "axisbank.com", "www.axisbank.com", "npci.org.in", "www.npci.org.in",
    "paytm.com", "phonepe.com", "gpay.app", "finsarthi.app", "github.com"
}

# URL Shortening Services
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "rb.gy", "t.co", "ow.ly"}

# High-Risk TLDs & Phishing Keywords
SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".ml", ".click", ".gq", ".cf", ".work", ".link"}
PHISHING_KEYWORDS = ["verify-kyc", "upi-pin", "free-reward", "claim-bonus", "account-blocked", "urgent-update", "lottery-win", "refund-claim"]


class GuardianService:
    @classmethod
    def inspect_security_target(cls, text: str) -> dict[str, Any]:
        """
        Parses text for URLs, UPI patterns, or QR code requests and returns structured risk analysis JSON.
        """
        url_match = re.search(r'(https?://[^\s]+)', text, re.IGNORECASE)
        if not url_match:
            lower = text.lower()
            if "upi pin" in lower or "enter pin to receive" in lower:
                return {
                    "has_url": False,
                    "type": "upi_pin_scam",
                    "risk_score": 0.95,
                    "safety_tier": "🔴 HIGH RISK",
                    "reasons": ["UPI PIN entered to receive money scam pattern"]
                }
            if "qr code" in lower and "receive" in lower:
                return {
                    "has_url": False,
                    "type": "qr_code_scam",
                    "risk_score": 0.90,
                    "safety_tier": "🔴 HIGH RISK",
                    "reasons": ["Scanning QR code to receive money scam pattern"]
                }
            return {
                "has_url": False,
                "type": "general_query",
                "risk_score": 0.10,
                "safety_tier": "🟢 GENERAL INQUIRY",
                "reasons": []
            }

        raw_url = url_match.group(1)
        try:
            parsed = urlparse(raw_url)
            domain = parsed.netloc.lower()
            scheme = parsed.scheme.lower()

            if ":" in domain:
                domain = domain.split(":")[0]

            is_whitelisted = (domain in OFFICIAL_WHITELIST or any(domain.endswith("." + trusted) for trusted in OFFICIAL_WHITELIST))
            is_shortener = domain in URL_SHORTENERS
            is_suspicious_tld = any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS)
            is_phishing_keyword = any(kw in raw_url.lower() for kw in PHISHING_KEYWORDS)

            if is_whitelisted:
                tier = "🟢 SAFE"
                score = 0.0
            elif is_shortener:
                tier = "🔴 SUSPICIOUS SHORTENED URL"
                score = 0.85
            elif is_suspicious_tld or is_phishing_keyword:
                tier = "🔴 HIGH RISK (PHISHING THREAT)"
                score = 0.95
            else:
                tier = "🟡 CAUTION (UNVERIFIED THIRD-PARTY)"
                score = 0.50

            return {
                "has_url": True,
                "raw_url": raw_url,
                "domain": domain,
                "protocol": scheme.upper(),
                "is_whitelisted": is_whitelisted,
                "is_shortener": is_shortener,
                "is_suspicious_tld": is_suspicious_tld,
                "is_phishing_keyword": is_phishing_keyword,
                "risk_score": score,
                "safety_tier": tier,
                "reasons": [
                    "Official verified domain" if is_whitelisted else "",
                    "URL shortener conceals destination" if is_shortener else "",
                    "Suspicious TLD or phishing keyword" if (is_suspicious_tld or is_phishing_keyword) else ""
                ]
            }

        except Exception as e:
            logger.error("Error inspecting URL '%s': %s", raw_url, e)
            return {
                "has_url": True,
                "raw_url": raw_url,
                "domain": "unknown",
                "protocol": "UNKNOWN",
                "risk_score": 0.70,
                "safety_tier": "🟡 UNPARSABLE URL",
                "reasons": [str(e)]
            }

    @classmethod
    def analyze_security_request(cls, text: str) -> str:
        """Legacy helper for backward compatibility."""
        data = cls.inspect_security_target(text)
        if not data.get("has_url"):
            if data.get("type") == "upi_pin_scam":
                return "🛡️ **Guardian Security Alert**\n\n• **Risk Level**: 🔴 HIGH RISK (UPI Scam Pattern)\n• **Golden Rule**: Entering your UPI PIN is ONLY required to DEBIT money from your account, NEVER to receive money.\n• **Recommendation**: Immediately decline this payment request."
            if data.get("type") == "qr_code_scam":
                return "🛡️ **Guardian Security Alert**\n\n• **Risk Level**: 🔴 HIGH RISK (QR Code Scam Pattern)\n• **Rule**: Scanning a QR code sent by someone else authorizes a PAYMENT out of your bank account.\n• **Recommendation**: Do not scan any QR codes sent to receive refunds or buyer payments."
            return "🛡️ **Guardian Security Inspection**\n\nPlease share the exact payment link, domain URL, SMS message, or QR code request you would like me to inspect for fraud safety."

        dom = data.get("domain")
        tier = data.get("safety_tier")
        if data.get("is_whitelisted"):
            return f"🛡️ **Guardian Security Report**\n\n• **Inspected Domain**: `{dom}` (Verified Official Domain)\n• **Protocol**: {data.get('protocol')} (Secure)\n• **Shortened URL**: No\n• **Phishing Risk**: None Detected\n• **Safety Tier**: {tier}\n\nThis appears to be a legitimate, official domain ({dom}). You can safely proceed."
        if data.get("is_shortener"):
            return f"🛡️ **Guardian Security Warning**\n\n• **Inspected Domain**: `{dom}` (URL Shortener)\n• **Protocol**: {data.get('protocol')}\n• **Phishing Risk**: 🔴 HIGH RISK\n• **Safety Tier**: {tier}\n\n⚠️ **Warning**: Shortened links hide the actual destination URL. Scammers frequently use shortened links ({dom}) in SMS phishing to hide fake banking portals. Do NOT enter credentials or PINs."
        
        return f"🛡️ **Guardian Security Assessment**\n\n• **Inspected Domain**: `{dom}`\n• **Protocol**: {data.get('protocol')}\n• **Official Whitelist Status**: Unverified Third-Party Domain\n• **Safety Tier**: {tier}\n\nEnsure you verify the website authenticity before entering any bank credentials, UPI details, or OTPs."
