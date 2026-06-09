"""
Khushi Decors SQLAlchemy models.
Maps to existing PostgreSQL tables created by db.py migrations.
"""
import uuid
from datetime import datetime
from extensions import db_sql as db


class ORMBase:
    def __init__(self, **kwargs):
        # Allow arbitrary keyword arguments for static analysis type compatibility
        for k, v in kwargs.items():
            setattr(self, k, v)


def gen_uuid():
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# User
# ═══════════════════════════════════════════════════════════════════════════════

class User(db.Model, ORMBase):
    __tablename__ = "users"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    first_name    = db.Column(db.String, default="")
    last_name     = db.Column(db.String, default="")
    email         = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role          = db.Column(db.String, default="customer")
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class UserAddress(db.Model, ORMBase):
    __tablename__ = "user_addresses"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    user_id       = db.Column(db.String, nullable=False)
    label         = db.Column(db.String, default="Home")
    first_name    = db.Column(db.String, default="")
    last_name     = db.Column(db.String, default="")
    phone         = db.Column(db.String, default="")
    address_line1 = db.Column(db.String, nullable=False, default="")
    address_line2 = db.Column(db.String, default="")
    city          = db.Column(db.String, default="")
    state         = db.Column(db.String, default="")
    pincode       = db.Column(db.String, default="")
    country       = db.Column(db.String, default="India")
    is_default    = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Product
# ═══════════════════════════════════════════════════════════════════════════════

class Category(db.Model, ORMBase):
    __tablename__ = "categories"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    name          = db.Column(db.String, nullable=False)
    slug          = db.Column(db.String, unique=True, nullable=False)
    parent_id     = db.Column(db.String, db.ForeignKey("categories.id"))
    image_url     = db.Column(db.String, default="")
    is_active     = db.Column(db.Integer, default=1)
    is_featured   = db.Column(db.Integer, default=0)
    display_order = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    children      = db.relationship("Category", backref=db.backref("parent", remote_side=[id]))


class Brand(db.Model, ORMBase):
    __tablename__ = "brands"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    name          = db.Column(db.String, nullable=False)
    slug          = db.Column(db.String, unique=True, nullable=False)
    image_url     = db.Column(db.String, default="")
    is_active     = db.Column(db.Integer, default=1)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Attribute(db.Model, ORMBase):
    __tablename__ = "attributes"
    id             = db.Column(db.String, primary_key=True, default=gen_uuid)
    name           = db.Column(db.String, nullable=False)
    slug           = db.Column(db.String, unique=True, nullable=False)
    display_order  = db.Column(db.Integer, default=0)
    variation_type = db.Column(db.String, default="secondary")


class AttributeValue(db.Model, ORMBase):
    __tablename__ = "attribute_values"
    id             = db.Column(db.String, primary_key=True, default=gen_uuid)
    attribute_id   = db.Column(db.String, db.ForeignKey("attributes.id"), nullable=False)
    value          = db.Column(db.String, nullable=False)
    image_url      = db.Column(db.String, default="")
    display_order  = db.Column(db.Integer, default=0)
    attribute      = db.relationship("Attribute", backref="values")


class Media(db.Model, ORMBase):
    __tablename__ = "media"
    id         = db.Column(db.String, primary_key=True, default=gen_uuid)
    file_url   = db.Column(db.String, nullable=False)
    alt_text   = db.Column(db.String, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model, ORMBase):
    __tablename__ = "products"
    id                = db.Column(db.String, primary_key=True, default=gen_uuid)
    name              = db.Column(db.String, nullable=False)
    slug              = db.Column(db.String, unique=True, nullable=False)
    sku               = db.Column(db.String, unique=True)
    type              = db.Column(db.String, default="simple")
    short_description = db.Column(db.String, default="")
    description       = db.Column(db.String, default="")
    price             = db.Column(db.Numeric(10, 2), default=0)
    sale_price        = db.Column(db.Numeric(10, 2))
    stock_quantity    = db.Column(db.Integer, default=0)
    stock_status      = db.Column(db.String, default="in_stock")
    category_id       = db.Column(db.String, db.ForeignKey("categories.id"))
    brand_id          = db.Column(db.String, db.ForeignKey("brands.id"))
    is_active         = db.Column(db.Integer, default=1)
    is_featured       = db.Column(db.Integer, default=0)
    family_id         = db.Column(db.String, db.ForeignKey("products.id"))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow)
    category          = db.relationship("Category", backref="products")
    brand             = db.relationship("Brand", backref="products")
    images            = db.relationship("ProductImage", backref="product", lazy="dynamic")
    variations        = db.relationship("ProductVariation", backref="product", lazy="dynamic")


class ProductImage(db.Model, ORMBase):
    __tablename__ = "product_images"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    product_id    = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    media_id      = db.Column(db.String, db.ForeignKey("media.id"), nullable=False)
    is_primary    = db.Column(db.Integer, default=0)
    display_order = db.Column(db.Integer, default=0)
    media         = db.relationship("Media")


class ProductVariation(db.Model, ORMBase):
    __tablename__ = "product_variations"
    id                = db.Column(db.String, primary_key=True, default=gen_uuid)
    product_id        = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    sku               = db.Column(db.String)
    price             = db.Column(db.Numeric(10, 2), default=0)
    sale_price        = db.Column(db.Numeric(10, 2))
    stock_quantity    = db.Column(db.Integer, default=0)
    stock_status      = db.Column(db.String, default="in_stock")
    name              = db.Column(db.String, default="")
    short_description = db.Column(db.String, default="")
    description       = db.Column(db.String, default="")
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)


class VariationAttributeValue(db.Model, ORMBase):
    __tablename__ = "variation_attribute_values"
    id                 = db.Column(db.String, primary_key=True, default=gen_uuid)
    variation_id       = db.Column(db.String, db.ForeignKey("product_variations.id"), nullable=False)
    attribute_value_id = db.Column(db.String, db.ForeignKey("attribute_values.id"), nullable=False)


class ProductAttribute(db.Model, ORMBase):
    __tablename__ = "product_attributes"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    product_id    = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    attribute_id  = db.Column(db.String, db.ForeignKey("attributes.id"), nullable=False)
    display_order = db.Column(db.Integer, default=0)


class ProductAttributeValue(db.Model, ORMBase):
    __tablename__ = "product_attribute_values"
    id                 = db.Column(db.String, primary_key=True, default=gen_uuid)
    product_id         = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    attribute_value_id = db.Column(db.String, db.ForeignKey("attribute_values.id"), nullable=False)


class VariationImage(db.Model, ORMBase):
    __tablename__ = "variation_images"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    variation_id  = db.Column(db.String, db.ForeignKey("product_variations.id"), nullable=False)
    media_id      = db.Column(db.String, db.ForeignKey("media.id"), nullable=False)
    is_primary    = db.Column(db.Integer, default=0)
    display_order = db.Column(db.Integer, default=0)


# ═══════════════════════════════════════════════════════════════════════════════
# Order
# ═══════════════════════════════════════════════════════════════════════════════

class Order(db.Model, ORMBase):
    __tablename__ = "orders"
    id                   = db.Column(db.String, primary_key=True, default=gen_uuid)
    user_id              = db.Column(db.String, db.ForeignKey("users.id"))
    status               = db.Column(db.String, default="pending")
    total_amount         = db.Column(db.Numeric(10, 2), default=0)
    payment_method       = db.Column(db.String, default="cod")
    payment_status       = db.Column(db.String, default="pending")
    order_number         = db.Column(db.String)
    coupon_code          = db.Column(db.String, default="")
    discount_amount      = db.Column(db.Numeric(10, 2), default=0)
    subtotal             = db.Column(db.Numeric(10, 2), default=0)
    shipping_amount      = db.Column(db.Numeric(10, 2), default=0)
    shipping_address_json = db.Column(db.String, default="")
    customer_name        = db.Column(db.String, default="")
    customer_email       = db.Column(db.String, default="")
    customer_phone       = db.Column(db.String, default="")
    notes                = db.Column(db.String, default="")
    cancelled_at         = db.Column(db.DateTime)
    cancel_reason        = db.Column(db.String, default="")
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at           = db.Column(db.DateTime, default=datetime.utcnow)


class OrderItem(db.Model, ORMBase):
    __tablename__ = "order_items"
    id                   = db.Column(db.String, primary_key=True, default=gen_uuid)
    order_id             = db.Column(db.String, db.ForeignKey("orders.id"), nullable=False)
    product_id           = db.Column(db.String, db.ForeignKey("products.id"))
    variation_id         = db.Column(db.String)
    quantity             = db.Column(db.Integer, default=1)
    unit_price           = db.Column(db.Numeric(10, 2), default=0)
    total_price          = db.Column(db.Numeric(10, 2), default=0)
    product_name_snapshot = db.Column(db.String, default="")
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)


class Coupon(db.Model, ORMBase):
    __tablename__ = "coupons"
    id                   = db.Column(db.String, primary_key=True, default=gen_uuid)
    code                 = db.Column(db.String, unique=True, nullable=False)
    type                 = db.Column(db.String, default="percent")
    value                = db.Column(db.Numeric(10, 2), default=0)
    min_order            = db.Column(db.Numeric(10, 2), default=0)
    min_order_amount     = db.Column(db.Numeric(10, 2), default=0)
    max_uses             = db.Column(db.Integer, default=0)
    usage_limit          = db.Column(db.Integer)
    usage_limit_per_user = db.Column(db.Integer, default=1)
    per_user             = db.Column(db.Integer, default=1)
    max_discount         = db.Column(db.Numeric(10, 2))
    is_active            = db.Column(db.Integer, default=1)
    expires_at           = db.Column(db.DateTime)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)


class CouponUsage(db.Model, ORMBase):
    __tablename__ = "coupon_usages"
    id         = db.Column(db.String, primary_key=True, default=gen_uuid)
    coupon_id  = db.Column(db.String, nullable=False)
    user_id    = db.Column(db.String, nullable=False)
    order_id   = db.Column(db.String, nullable=False)
    used_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Blog
# ═══════════════════════════════════════════════════════════════════════════════

class BlogPost(db.Model, ORMBase):
    __tablename__ = "blog_posts"
    id         = db.Column(db.String, primary_key=True, default=gen_uuid)
    title      = db.Column(db.String, nullable=False)
    slug       = db.Column(db.String, unique=True, nullable=False)
    excerpt    = db.Column(db.String, default="")
    content    = db.Column(db.String, default="")
    image_url  = db.Column(db.String, default="")
    author     = db.Column(db.String, default="Admin")
    published  = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Store / Other
# ═══════════════════════════════════════════════════════════════════════════════

class StoreSetting(db.Model, ORMBase):
    __tablename__ = "store_settings"
    key        = db.Column(db.String, primary_key=True)
    value      = db.Column(db.String, nullable=False, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model, ORMBase):
    __tablename__ = "newsletter_subscribers"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    email         = db.Column(db.String, unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProductReview(db.Model, ORMBase):
    __tablename__ = "product_reviews"
    id          = db.Column(db.String, primary_key=True, default=gen_uuid)
    product_id  = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    user_id     = db.Column(db.String, db.ForeignKey("users.id"))
    rating      = db.Column(db.Integer, default=5)
    title       = db.Column(db.String, default="")
    body        = db.Column(db.String, default="")
    is_approved = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)



class ContactMessage(db.Model, ORMBase):
    __tablename__ = "contact_messages"
    id         = db.Column(db.String, primary_key=True, default=gen_uuid)
    name       = db.Column(db.String, nullable=False, default="")
    email      = db.Column(db.String, nullable=False, default="")
    message    = db.Column(db.String, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# Style Planner (Homepage "Choose Collection Style" section)
# ═══════════════════════════════════════════════════════════════════════════════

class PlannerCollection(db.Model, ORMBase):
    __tablename__ = "planner_collections"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    title         = db.Column(db.String, nullable=False)
    tip           = db.Column(db.String, default="")
    image_url     = db.Column(db.String, default="")
    page_slug     = db.Column(db.String, default="")   # used in /shop?category=<slug>
    display_order = db.Column(db.Integer, default=0)
    is_active     = db.Column(db.Integer, default=1)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    col_products  = db.relationship(
        "PlannerCollectionProduct", backref="collection",
        lazy="dynamic", cascade="all, delete-orphan",
        order_by="PlannerCollectionProduct.display_order"
    )


class PlannerCollectionProduct(db.Model, ORMBase):
    __tablename__ = "planner_collection_products"
    id            = db.Column(db.String, primary_key=True, default=gen_uuid)
    collection_id = db.Column(db.String, db.ForeignKey("planner_collections.id"), nullable=False)
    product_id    = db.Column(db.String, db.ForeignKey("products.id"), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    product       = db.relationship("Product")


