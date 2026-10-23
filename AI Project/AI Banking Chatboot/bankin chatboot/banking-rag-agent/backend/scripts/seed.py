"""Seed database with demo users and ingest sample banking documents."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth.security import hash_password
from app.config import get_settings
from app.database.mongodb import close_db, connect_db, get_collection
from app.services.document_service import ingest_document
from app.utils.helpers import generate_id, utc_now


SAMPLE_DOCS = [
    ("Bank_FAQ.txt", "General FAQ"),
    ("Account_Opening_Guidelines.txt", "Account"),
    ("KYC_Policy.txt", "KYC"),
    ("Credit_Card_Policy.txt", "Credit Card"),
    ("Debit_Card_Policy.txt", "Debit Card"),
    ("Personal_Loan_Policy.txt", "Loan"),
    ("Home_Loan_Policy.txt", "Loan"),
    ("Education_Loan_Policy.txt", "Loan"),
    ("Interest_Rates.txt", "Interest Rates"),
    ("Banking_Charges.txt", "Banking Charges"),
    ("Fund_Transfer_Guidelines.txt", "Fund Transfer"),
    ("Internet_Mobile_Banking.txt", "General FAQ"),
    ("Complaint_Dispute_Procedures.txt", "Complaints"),
]


async def seed_users():
    users = get_collection("users")
    demo_users = [
        {
            "_id": "usr_demo_customer",
            "name": "Rajesh Kumar",
            "email": "demo@customer.com",
            "password_hash": hash_password("demo123"),
            "role": "customer",
            "created_at": utc_now(),
        },
        {
            "_id": "usr_demo_admin",
            "name": "Admin User",
            "email": "admin@demobank.com",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "created_at": utc_now(),
        },
    ]
    for user in demo_users:
        existing = await users.find_one({"email": user["email"]})
        if not existing:
            await users.insert_one(user)
            print(f"  Created user: {user['email']} ({user['role']})")
        else:
            print(f"  User exists: {user['email']}")


async def seed_documents():
    docs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "documents"
    if not docs_dir.exists():
        print(f"  Documents directory not found: {docs_dir}")
        return

    for filename, category in SAMPLE_DOCS:
        file_path = docs_dir / filename
        if not file_path.exists():
            print(f"  Skipping missing file: {filename}")
            continue

        existing = await get_collection("documents").find_one({"filename": filename})
        if existing:
            print(f"  Document already indexed: {filename}")
            continue

        try:
            result = await ingest_document(str(file_path), filename, category, "usr_demo_admin")
            print(f"  Indexed: {filename} ({result.get('chunk_count', 0)} chunks)")
        except Exception as exc:
            print(f"  Failed to index {filename}: {exc}")


async def main():
    print("Seeding Banking RAG Agent database...")
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.vector_store_path, exist_ok=True)

    await connect_db()
    try:
        print("\n[1/2] Seeding users...")
        await seed_users()
        print("\n[2/2] Ingesting sample documents...")
        await seed_documents()
        print("\nSeed complete!")
        print("\nDemo credentials:")
        print("  Customer: demo@customer.com / demo123")
        print("  Admin:    admin@demobank.com / admin123")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
