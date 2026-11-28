"""Menu items (dishes).

Guardrails (database-enforced):
  * price is whole paise, 0 .. ₹10,000; prep time 1..180 minutes
  * name unique (case-insensitive) and non-empty
  * items are never deleted (orders point at them); set is_active = false instead
"""

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Identity, Index, Integer, Text, func
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin

MAX_ITEM_PRICE_PAISE = 1_000_000  # ₹10,000 per item: anything above is a typo


class MenuItem(TimestampMixin, Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 80", name="name_length"),
        CheckConstraint(
            f"price_paise BETWEEN 0 AND {MAX_ITEM_PRICE_PAISE}", name="price_paise_range"
        ),
        CheckConstraint("prep_minutes BETWEEN 1 AND 180", name="prep_minutes_range"),
        Index("uq_menu_items_name_lower", func.lower(sql_text("name")), unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    # Typical cooking time; later learned from real kitchen data
    prep_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sql_text("true")
    )
