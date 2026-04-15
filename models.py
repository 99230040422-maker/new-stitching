from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from .database import Base
except ImportError:
    from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    image_url: Mapped[str] = mapped_column(String(400), nullable=False)
    sizes_csv: Mapped[str] = mapped_column(String(100), nullable=False)
    colors_csv: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(140), nullable=False)
    product_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_size: Mapped[str] = mapped_column(String(20), nullable=False)
    selected_color: Mapped[str] = mapped_column(String(40), nullable=False)
    logo_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_image_url: Mapped[str | None] = mapped_column(String(400), nullable=True)
    logo_placement: Mapped[str] = mapped_column(String(40), nullable=False)
    custom_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Pending", nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")
