"""Import every module's models here so Alembic and tests see all tables."""

from app.core.models import Base
from app.modules.audit.models import AuditLog

__all__ = ["AuditLog", "Base"]
