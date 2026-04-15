from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Literal["owner", "user"]


class SignUpRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    phone: str | None = None
    address: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    category: str
    image_url: str
    sizes: list[str]
    colors: list[str]
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)


class ProductUpdate(ProductCreate):
    pass


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    image_url: str
    sizes: list[str]
    colors: list[str]
    price: float
    stock: int
    is_out_of_stock: bool
    is_low_stock: bool


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    selected_size: str
    selected_color: str
    logo_text: str | None = None
    logo_image_url: str | None = None
    logo_placement: Literal[
        "front center", "left chest", "right chest", "back center", "sleeve"
    ]
    custom_instruction: str | None = None


class OrderOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    selected_size: str
    selected_color: str
    logo_text: str | None
    logo_image_url: str | None
    logo_placement: str
    custom_instruction: str | None
    status: str
    order_date: datetime


class UpdateOrderStatus(BaseModel):
    status: Literal["Pending", "Processing", "Delivered", "Cancelled"]


class DashboardStats(BaseModel):
    total_products: int
    total_orders: int
    total_users: int
    pending_orders: int
    low_stock_count: int
