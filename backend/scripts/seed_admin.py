#!/usr/bin/env python3
"""
Seed an initial admin user into the database.

Usage (from the backend/ directory):
    python scripts/seed_admin.py

Environment variables are read from the .env file (or the shell environment).
Run AFTER 'alembic upgrade head'.
"""

import asyncio
import os
import sys

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole

SEED_USERS = [
    {
        "name": "Admin User",
        "email": "admin@vidshield.ai",
        "password": "password123",
        "role": UserRole.ADMIN,
        "tenant_id": "org-vidshield-demo",
    },
    {
        "name": "Operator User",
        "email": "operator@vidshield.ai",
        "password": "password123",
        "role": UserRole.OPERATOR,
        "tenant_id": "org-vidshield-demo",
    },
]


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        for data in SEED_USERS:
            existing = await session.execute(select(User).where(User.email == data["email"]))
            if existing.scalar_one_or_none():
                print(f"  [skip]   {data['email']} already exists")
                continue

            user = User(
                email=data["email"],
                name=data["name"],
                password_hash=hash_password(data["password"]),
                role=data["role"],
                tenant_id=data["tenant_id"],
            )
            session.add(user)
            print(f"  [create] {data['email']}  role={data['role'].value}")

        await session.commit()

    await engine.dispose()
    print("\nSeeding complete.")


if __name__ == "__main__":
    print("Seeding admin users...")
    asyncio.run(seed())
