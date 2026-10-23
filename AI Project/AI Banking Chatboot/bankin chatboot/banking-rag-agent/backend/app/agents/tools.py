"""Mock banking API tools with synthetic demo data."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.utils.helpers import generate_id, utc_now

SYNTHETIC_CUSTOMERS = {
    "demo@customer.com": {
        "customer_id": "CUST-10001",
        "name": "Rajesh Kumar",
        "account_number": "****4521",
        "account_type": "Savings",
        "balance": 125430.50,
        "branch": "Mumbai Main Branch",
        "kyc_status": "Verified",
        "phone": "+91-98765-43210",
    },
    "admin@demobank.com": {
        "customer_id": "CUST-10002",
        "name": "Admin User",
        "account_number": "****7890",
        "account_type": "Current",
        "balance": 500000.00,
        "branch": "Delhi HQ",
        "kyc_status": "Verified",
        "phone": "+91-98765-00001",
    },
}

SYNTHETIC_TRANSACTIONS = {
    "CUST-10001": [
        {"date": "2026-09-08", "description": "UPI Payment - Amazon", "amount": -2499.00, "type": "debit"},
        {"date": "2026-09-07", "description": "Salary Credit - TechCorp", "amount": 75000.00, "type": "credit"},
        {"date": "2026-09-05", "description": "ATM Withdrawal", "amount": -5000.00, "type": "debit"},
        {"date": "2026-09-03", "description": "NEFT Transfer - Rent", "amount": -18000.00, "type": "debit"},
        {"date": "2026-09-01", "description": "Interest Credit", "amount": 342.50, "type": "credit"},
    ],
    "CUST-10002": [
        {"date": "2026-09-08", "description": "Vendor Payment", "amount": -45000.00, "type": "debit"},
        {"date": "2026-09-06", "description": "Client Receipt", "amount": 120000.00, "type": "credit"},
    ],
}

SYNTHETIC_LOANS = {
    "CUST-10001": {
        "loan_id": "LN-2024-8871",
        "type": "Personal Loan",
        "amount": 500000.00,
        "outstanding": 312450.00,
        "emi": 12450.00,
        "next_due": "2026-09-15",
        "status": "Active",
    },
}

TICKETS_STORE: List[Dict[str, Any]] = []


def _get_customer(email: str) -> Optional[dict]:
    return SYNTHETIC_CUSTOMERS.get(email)


def get_account_balance(user_email: str) -> str:
    customer = _get_customer(user_email)
    if not customer:
        return "I couldn't retrieve your account information. Please contact support."

    return (
        f"Your {customer['account_type']} account (ending {customer['account_number'][-4:]}) "
        f"has an available balance of ₹{customer['balance']:,.2f} as of today."
    )


def get_recent_transactions(user_email: str, limit: int = 5) -> str:
    customer = _get_customer(user_email)
    if not customer:
        return "I couldn't retrieve your transaction history."

    txns = SYNTHETIC_TRANSACTIONS.get(customer["customer_id"], [])[:limit]
    if not txns:
        return "No recent transactions found for your account."

    lines = ["Here are your recent transactions:\n"]
    for t in txns:
        sign = "+" if t["type"] == "credit" else "-"
        lines.append(f"• {t['date']}: {t['description']} — {sign}₹{abs(t['amount']):,.2f}")
    return "\n".join(lines)


def get_customer_profile(user_email: str) -> str:
    customer = _get_customer(user_email)
    if not customer:
        return "I couldn't retrieve your profile information."

    return (
        f"Customer Profile:\n"
        f"• Name: {customer['name']}\n"
        f"• Account: {customer['account_type']} ({customer['account_number']})\n"
        f"• Branch: {customer['branch']}\n"
        f"• KYC Status: {customer['kyc_status']}\n"
        f"• Registered Phone: {customer['phone']}"
    )


def get_loan_status(user_email: str) -> str:
    customer = _get_customer(user_email)
    if not customer:
        return "I couldn't retrieve your loan information."

    loan = SYNTHETIC_LOANS.get(customer["customer_id"])
    if not loan:
        return "You don't have any active loans with DemoBank."

    return (
        f"Loan Status ({loan['loan_id']}):\n"
        f"• Type: {loan['type']}\n"
        f"• Original Amount: ₹{loan['amount']:,.2f}\n"
        f"• Outstanding: ₹{loan['outstanding']:,.2f}\n"
        f"• Monthly EMI: ₹{loan['emi']:,.2f}\n"
        f"• Next Due Date: {loan['next_due']}\n"
        f"• Status: {loan['status']}"
    )


def create_support_ticket(user_email: str, issue: str, category: str = "General") -> dict:
    ticket_id = f"TKT-{generate_id('')[:5].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "user_email": user_email,
        "issue": issue,
        "category": category,
        "status": "open",
        "created_at": utc_now(),
        "resolution": None,
    }
    TICKETS_STORE.append(ticket)
    return ticket


def get_user_tickets(user_email: str) -> List[dict]:
    return [t for t in TICKETS_STORE if t.get("user_email") == user_email]
