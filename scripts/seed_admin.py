import asyncio
from getpass import getpass
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.db.database import async_session_factory
from src.models.user import User
from src.models.enums import UserRole
from src.core.security import hash_password

async def seed_admin():
    email = input("Admin Email: ").strip().lower()
    password = getpass("Admin Password: ")
    confirm_password = getpass("Confirm Password: ")

    if not email:
        print("Email is required")
        return

    if len(password) < 12:
        print("Use a password with atleast 12 characters")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    async with async_session_factory() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("A user with this email already exists.")
                return

            admin = User(
                email= email,
                password_hash= hash_password(password=password),
                role= UserRole.ADMIN,
                is_active= True,
            )

            session.add(admin)
            await session.commit()
            print(f"Admin user created successfully: {email}")

        except IntegrityError:
            await session.rollback()
            print("Could not create admin. The email may already exist.")

        except Exception:
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_admin())