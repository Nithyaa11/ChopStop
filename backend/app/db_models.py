"""Import every module's models here so Alembic and tests see all tables."""

from app.core.models import Base
from app.modules.audit.models import AuditLog
from app.modules.menu.models import MenuItem
from app.modules.orders.models import Order, OrderItem
from app.modules.users.models import User

__all__ = ["AuditLog", "Base", "MenuItem", "Order", "OrderItem", "User"]
