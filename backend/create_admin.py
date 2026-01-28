
import asyncio
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import async_session_context
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    """Create a default admin user if one doesn't exist."""
    print("Checking for existing admin user...")
    
    async with async_session_context() as db:
        # Check if any admin exists
        result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        admin = result.scalar_one_or_none()
        
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return
            
        print("Creating default admin user...")
        # Create admin user
        admin_email = "admin@example.com"
        admin_password = "admin123"
        admin_user = User(
            email=admin_email,
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash(admin_password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            theme="light"
        )
        
        db.add(admin_user)
        await db.commit()
        
        print("\n" + "="*50)
        print("ADMIN USER CREATED SUCCESSFULLY")
        print("="*50)
        print(f"Email:    {admin_email}")
        print(f"Password: {admin_password}")
        print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(create_admin())
