from sqlalchemy.orm import Session

try:
    from .auth import hash_password
    from .models import Product, User
except ImportError:
    from auth import hash_password
    from models import Product, User


def seed_data(db: Session) -> None:
    owner = db.query(User).filter(User.email == "owner@shop.com").first()
    if not owner:
        owner = User(
            full_name="Shop Owner",
            email="owner@shop.com",
            password_hash=hash_password("Owner@123"),
            is_owner=True,
        )
        db.add(owner)

    if db.query(Product).count() == 0:
        products = [
            Product(
                name="Signature Organic Tee",
                description="Premium organic cotton custom-ready t-shirt.",
                category="Organic",
                image_url="https://placehold.co/600x700/e9dfcf/3f2e24?text=Signature+Tee",
                sizes_csv="S,M,L,XL",
                colors_csv="Black,White,Oatmeal",
                price=39.0,
                stock=24,
                low_stock_threshold=5,
            ),
            Product(
                name="Urban Oversized Tee",
                description="Streetwear oversized fit for logo prints.",
                category="Oversized",
                image_url="https://placehold.co/600x700/d7cfbf/3d2f2a?text=Oversized+Tee",
                sizes_csv="M,L,XL",
                colors_csv="Charcoal,Stone,Navy",
                price=49.0,
                stock=14,
                low_stock_threshold=5,
            ),
            Product(
                name="Premium Polo Cotton",
                description="Clean polo silhouette for premium branding.",
                category="Polo",
                image_url="https://placehold.co/600x700/e4d5bf/473426?text=Premium+Polo",
                sizes_csv="S,M,L,XL",
                colors_csv="White,Navy,Olive",
                price=55.0,
                stock=8,
                low_stock_threshold=4,
            ),
        ]
        db.add_all(products)
    db.commit()
