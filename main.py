from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from .auth import create_access_token, get_current_user, hash_password, require_owner, verify_password
    from .database import Base, SessionLocal, engine, get_db
    from .models import Order, Product, User
    from .schemas import (
        DashboardStats,
        LoginRequest,
        OrderCreate,
        OrderOut,
        ProductCreate,
        ProductOut,
        ProductUpdate,
        SignUpRequest,
        TokenResponse,
        UpdateOrderStatus,
    )
    from .seed import seed_data
except ImportError:
    # Supports flat-module execution such as `uvicorn main:app`.
    from auth import create_access_token, get_current_user, hash_password, require_owner, verify_password
    from database import Base, SessionLocal, engine, get_db
    from models import Order, Product, User
    from schemas import (
        DashboardStats,
        LoginRequest,
        OrderCreate,
        OrderOut,
        ProductCreate,
        ProductOut,
        ProductUpdate,
        SignUpRequest,
        TokenResponse,
        UpdateOrderStatus,
    )
    from seed import seed_data

app = FastAPI(title="ThreadCraft API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def as_product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        category=p.category,
        image_url=p.image_url,
        sizes=[x.strip() for x in p.sizes_csv.split(",") if x.strip()],
        colors=[x.strip() for x in p.colors_csv.split(",") if x.strip()],
        price=p.price,
        stock=p.stock,
        is_out_of_stock=p.stock == 0,
        is_low_stock=(0 < p.stock <= p.low_stock_threshold),
    )


def as_order_out(o: Order) -> OrderOut:
    return OrderOut(
        id=o.id,
        user_id=o.user_id,
        user_name=o.user.full_name,
        user_email=o.user.email,
        product_id=o.product_id,
        product_name=o.product_name,
        product_price=o.product_price,
        quantity=o.quantity,
        selected_size=o.selected_size,
        selected_color=o.selected_color,
        logo_text=o.logo_text,
        logo_image_url=o.logo_image_url,
        logo_placement=o.logo_placement,
        custom_instruction=o.custom_instruction,
        status=o.status,
        order_date=o.order_date,
    )


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)


@app.post("/api/auth/signup", response_model=TokenResponse)
def user_signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        address=payload.address,
        is_owner=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, "user"), role="user")


@app.post("/api/auth/user-login", response_model=TokenResponse)
def user_login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_owner.is_(False)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id, "user"), role="user")


@app.post("/api/auth/owner-login", response_model=TokenResponse)
def owner_login(payload: LoginRequest, db: Session = Depends(get_db)):
    owner = db.query(User).filter(User.email == payload.email, User.is_owner.is_(True)).first()
    if not owner or not verify_password(payload.password, owner.password_hash):
        raise HTTPException(status_code=401, detail="Invalid owner credentials")
    return TokenResponse(access_token=create_access_token(owner.id, "owner"), role="owner")


@app.get("/api/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return [as_product_out(p) for p in db.query(Product).order_by(Product.id.desc()).all()]


@app.post("/api/products", response_model=ProductOut)
def create_product(
    payload: ProductCreate, _: User = Depends(require_owner), db: Session = Depends(get_db)
):
    p = Product(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        image_url=payload.image_url,
        sizes_csv=",".join(payload.sizes),
        colors_csv=",".join(payload.colors),
        price=payload.price,
        stock=payload.stock,
        low_stock_threshold=payload.low_stock_threshold,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return as_product_out(p)


@app.put("/api/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    _: User = Depends(require_owner),
    db: Session = Depends(get_db),
):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    p.name = payload.name
    p.description = payload.description
    p.category = payload.category
    p.image_url = payload.image_url
    p.sizes_csv = ",".join(payload.sizes)
    p.colors_csv = ",".join(payload.colors)
    p.price = payload.price
    p.stock = payload.stock
    p.low_stock_threshold = payload.low_stock_threshold
    db.commit()
    db.refresh(p)
    return as_product_out(p)


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, _: User = Depends(require_owner), db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    return {"message": "Product deleted"}


@app.post("/api/orders", response_model=OrderOut)
def create_order(
    payload: OrderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.is_owner:
        raise HTTPException(status_code=403, detail="Owners cannot place customer orders")
    p = db.get(Product, payload.product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.quantity > p.stock:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available stock")
    if payload.selected_size not in [x.strip() for x in p.sizes_csv.split(",")]:
        raise HTTPException(status_code=400, detail="Invalid size for selected product")
    if payload.selected_color not in [x.strip() for x in p.colors_csv.split(",")]:
        raise HTTPException(status_code=400, detail="Invalid color for selected product")
    if not payload.logo_text and not payload.logo_image_url:
        raise HTTPException(status_code=400, detail="Provide logo image URL or logo text")

    order = Order(
        user_id=user.id,
        product_id=p.id,
        product_name=p.name,
        product_price=p.price,
        quantity=payload.quantity,
        selected_size=payload.selected_size,
        selected_color=payload.selected_color,
        logo_text=payload.logo_text,
        logo_image_url=payload.logo_image_url,
        logo_placement=payload.logo_placement,
        custom_instruction=payload.custom_instruction,
        status="Pending",
    )
    p.stock -= payload.quantity
    db.add(order)
    db.commit()
    db.refresh(order)
    return as_order_out(order)


@app.get("/api/orders/my", response_model=list[OrderOut])
def my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.is_owner:
        raise HTTPException(status_code=403, detail="Owner should use /api/orders/all")
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).all()
    return [as_order_out(o) for o in orders]


@app.get("/api/orders/all", response_model=list[OrderOut])
def all_orders(_: User = Depends(require_owner), db: Session = Depends(get_db)):
    return [as_order_out(o) for o in db.query(Order).order_by(Order.id.desc()).all()]


@app.patch("/api/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: UpdateOrderStatus,
    _: User = Depends(require_owner),
    db: Session = Depends(get_db),
):
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    o.status = payload.status
    db.commit()
    db.refresh(o)
    return as_order_out(o)


@app.get("/api/owner/dashboard", response_model=DashboardStats)
def owner_dashboard(_: User = Depends(require_owner), db: Session = Depends(get_db)):
    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(Product.stock > 0, Product.stock <= Product.low_stock_threshold)
        .scalar()
    )
    pending_orders = db.query(func.count(Order.id)).filter(Order.status == "Pending").scalar()
    return DashboardStats(
        total_products=db.query(func.count(Product.id)).scalar(),
        total_orders=db.query(func.count(Order.id)).scalar(),
        total_users=db.query(func.count(User.id)).filter(User.is_owner.is_(False)).scalar(),
        pending_orders=pending_orders,
        low_stock_count=low_stock_count,
    )


@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "role": "owner" if user.is_owner else "user",
    }
