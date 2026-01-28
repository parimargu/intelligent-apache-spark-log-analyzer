
import structlog
from sqlalchemy import select

from app.db import async_session_context
from app.models.user import User, UserRole
from app.core.security import get_password_hash

logger = structlog.get_logger()

async def ensure_admin_user():
    """Create a default admin user if one doesn't exist."""
    async with async_session_context() as db:
        try:
            # Check if any admin exists
            result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
            admin = result.scalar_one_or_none()
            
            if admin:
                logger.info("Admin user already exists")
                return
                
            logger.info("Creating default admin user")
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
            
            logger.info("Admin user created successfully", email=admin_email)
            
        except Exception as e:
            logger.error("Failed to seed admin user", error=str(e))
            # Don't raise, just log error so app can still start
