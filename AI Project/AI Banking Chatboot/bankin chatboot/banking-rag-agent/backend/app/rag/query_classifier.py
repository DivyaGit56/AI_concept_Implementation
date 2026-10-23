"""Query classification into banking categories."""

import re
from typing import Tuple

from app.schemas.schemas import QueryCategory

CATEGORY_PATTERNS = {
    QueryCategory.KYC: [
        r"\bkyc\b", r"identity verification", r"pan card", r"aadhaar",
        r"proof of address", r"verification document",
    ],
    QueryCategory.LOAN: [
        r"\bloan\b", r"personal loan", r"home loan", r"education loan",
        r"emi\b", r"eligibility", r"interest rate.*loan", r"mortgage",
    ],
    QueryCategory.CREDIT_CARD: [
        r"credit card", r"card limit", r"reward point", r"billing cycle",
    ],
    QueryCategory.DEBIT_CARD: [
        r"debit card", r"atm card", r"card not working", r"pin\b",
    ],
    QueryCategory.BANKING_CHARGES: [
        r"charge", r"fee", r"penalty", r"maintenance", r"minimum balance",
    ],
    QueryCategory.FUND_TRANSFER: [
        r"transfer", r"neft", r"rtgs", r"imps", r"upi", r"wire transfer",
    ],
    QueryCategory.INTEREST_RATES: [
        r"interest rate", r"fd rate", r"fixed deposit", r"savings rate",
    ],
    QueryCategory.COMPLAINTS: [
        r"complaint", r"dispute", r"grievance", r"escalat", r"not resolved",
    ],
    QueryCategory.ACCOUNT: [
        r"account", r"open account", r"savings account", r"current account",
        r"account opening", r"minimum balance",
    ],
    QueryCategory.ACCOUNT_DATA: [
        r"my balance", r"my transaction", r"my account", r"show my",
        r"recent transaction", r"account balance", r"loan status",
        r"my profile", r"customer profile",
    ],
}

ACCOUNT_DATA_PATTERNS = CATEGORY_PATTERNS[QueryCategory.ACCOUNT_DATA]


def classify_query(query: str) -> Tuple[QueryCategory, float]:
    query_lower = query.lower()
    scores: dict[QueryCategory, int] = {}

    for category, patterns in CATEGORY_PATTERNS.items():
        if category == QueryCategory.ACCOUNT_DATA:
            continue
        score = sum(1 for p in patterns if re.search(p, query_lower))
        if score > 0:
            scores[category] = score

    for pattern in ACCOUNT_DATA_PATTERNS:
        if re.search(pattern, query_lower):
            return QueryCategory.ACCOUNT_DATA, 0.95

    if not scores:
        return QueryCategory.GENERAL_FAQ, 0.5

    best = max(scores, key=scores.get)
    confidence = min(0.95, 0.5 + scores[best] * 0.15)
    return best, confidence
