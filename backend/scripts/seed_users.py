"""Seed the users allowlist.

Run:
    python -m scripts.seed_users

Edit USERS below to control who can sign in via Google.
Emails are case-insensitive and stored lowercase.
"""
from __future__ import annotations

from app.database import SessionLocal
from app.models.user import User

USERS: list[dict[str, str]] = [
    {"email": "ops.reviewer@medishield.demo", "name": "Ops Reviewer", "role": "REVIEWER"},
    {"email": "ops.admin@medishield.demo",    "name": "Ops Admin",    "role": "ADMIN"},
    # Add your own Gmail here for the demo:
    # {"email": "sandeeptiet@gmail.com",        "name": "Sandeep Kapoor","role": "ADMIN"},
]


def main() -> None:
    db = SessionLocal()
    try:
        created, updated = 0, 0
        for row in USERS:
            email = row["email"].lower()
            user = db.query(User).filter(User.email == email).one_or_none()
            if user is None:
                user = User(
                    email=email,
                    name=row["name"],
                    role=row["role"],
                    is_active=True,
                )
                db.add(user)
                created += 1
            else:
                user.name = row["name"]
                user.role = row["role"]
                user.is_active = True
                updated += 1
        db.commit()
        print(f"Seed complete. Created: {created}, Updated: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
