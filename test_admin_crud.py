"""
test_admin_crud.py — Comprehensive CRUD test suite for Khushi Decors Admin.
Run: python test_admin_crud.py
"""
import os
import sys
import uuid
import unittest
import bcrypt

# Set DATABASE_URL in environment before importing app.py to avoid SQLAlchemy URI missing error
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from extensions import db_sql
from models import (
    User, Category, Brand, Attribute, AttributeValue, Product,
    ProductAttribute, ProductAttributeValue, ProductVariation,
    VariationAttributeValue, VariationImage, Order, OrderItem,
    Coupon, CouponUsage, BlogPost, StoreSetting
)
from routes.admin import generate_variations, generate_unique_product_sku, generate_unique_variation_sku


class AdminCrudTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        # Use an in-memory SQLite database for testing, completely isolated
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        
        # Create all tables in the memory database
        db_sql.create_all()

    @classmethod
    def tearDownClass(cls):
        db_sql.session.remove()
        db_sql.drop_all()
        cls.ctx.pop()

    def setUp(self):
        # Create a clean state for each test by clear-seeding
        db_sql.drop_all()
        db_sql.create_all()
        
        # Setup logged-in admin user session
        self.setup_admin_user()

    def tearDown(self):
        db_sql.session.remove()

    def setup_admin_user(self):
        self.admin_email = "admin_test@khushidecors.com"
        admin = User.query.filter_by(email=self.admin_email).first()
        if not admin:
            pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
            admin = User(
                id=str(uuid.uuid4()),
                first_name="Admin",
                last_name="Test",
                email=self.admin_email,
                password_hash=pw,
                role="admin"
            )
            db_sql.session.add(admin)
            db_sql.session.commit()
            
        with self.client.session_transaction() as sess:
            sess["user"] = {
                "id": admin.id,
                "first_name": admin.first_name,
                "last_name": admin.last_name,
                "email": admin.email,
                "role": admin.role
            }

    # ── Test Cases ────────────────────────────────────────────────────────────

    def test_category_crud(self):
        # 1. Create Category
        resp = self.client.post("/admin/categories/new", data={
            "name": "Wall Art",
            "slug": "wall-art",
            "parent_id": "",
            "is_featured": "on"
        })
        self.assertEqual(resp.status_code, 302) # Redirect to index on success
        
        cat = Category.query.filter_by(slug="wall-art").first()
        self.assertIsNotNone(cat)
        self.assertEqual(cat.name, "Wall Art")
        self.assertEqual(cat.is_featured, 1)

        # 2. Edit Category
        resp = self.client.post(f"/admin/categories/{cat.id}/edit", data={
            "name": "Luxury Wall Art",
            "slug": "luxury-wall-art",
            "parent_id": "",
            "is_featured": ""
        })
        self.assertEqual(resp.status_code, 302)
        
        # Refresh and verify
        db_sql.session.refresh(cat)
        self.assertEqual(cat.name, "Luxury Wall Art")
        self.assertEqual(cat.slug, "luxury-wall-art")
        self.assertEqual(cat.is_featured, 0)

        # 3. Delete Category (Cascade/Decouple check)
        # Create a subcategory and a product inside it to check parent/child decoupling
        sub_cat = Category(id=str(uuid.uuid4()), name="Metal Art", slug="metal-art", parent_id=cat.id)
        prod = Product(id=str(uuid.uuid4()), name="Gold Sunburst", slug="gold-sunburst", sku="KD-GS-001", price=1999, category_id=cat.id)
        db_sql.session.add_all([sub_cat, prod])
        db_sql.session.commit()

        resp = self.client.post(f"/admin/categories/{cat.id}/delete")
        self.assertEqual(resp.status_code, 302)

        # Verify parent category is deleted
        deleted_cat = db_sql.session.get(Category, cat.id)
        self.assertIsNone(deleted_cat)

        # Verify child category parent_id is decoupled (set to None)
        db_sql.session.refresh(sub_cat)
        self.assertIsNone(sub_cat.parent_id)

        # Verify product category_id is decoupled (set to None)
        db_sql.session.refresh(prod)
        self.assertIsNone(prod.category_id)

    def test_brand_crud(self):
        # 1. Create Brand
        resp = self.client.post("/admin/brands/new", data={
            "name": "Clay Studio",
            "slug": "clay-studio"
        })
        self.assertEqual(resp.status_code, 302)
        
        brand = Brand.query.filter_by(slug="clay-studio").first()
        self.assertIsNotNone(brand)
        self.assertEqual(brand.name, "Clay Studio")

        # 2. Edit Brand
        resp = self.client.post(f"/admin/brands/{brand.id}/edit", data={
            "name": "Clay Studio Pro",
            "slug": "clay-studio-pro"
        })
        self.assertEqual(resp.status_code, 302)
        
        db_sql.session.refresh(brand)
        self.assertEqual(brand.name, "Clay Studio Pro")

        # 3. Delete Brand (Decouple check)
        prod = Product(id=str(uuid.uuid4()), name="Terracotta Pot", slug="terracotta-pot", sku="KD-TP-001", price=599, brand_id=brand.id)
        db_sql.session.add(prod)
        db_sql.session.commit()

        resp = self.client.post(f"/admin/brands/{brand.id}/delete")
        self.assertEqual(resp.status_code, 302)

        # Verify brand is deleted
        deleted_brand = db_sql.session.get(Brand, brand.id)
        self.assertIsNone(deleted_brand)

        # Verify product brand_id is decoupled (set to None)
        db_sql.session.refresh(prod)
        self.assertIsNone(prod.brand_id)

    def test_attribute_and_value_crud(self):
        # 1. Create Attribute
        resp = self.client.post("/admin/attributes/new", data={
            "name": "Color",
            "slug": "color",
            "variation_type": "primary"
        })
        self.assertEqual(resp.status_code, 302)
        
        attr = Attribute.query.filter_by(slug="color").first()
        self.assertIsNotNone(attr)
        self.assertEqual(attr.name, "Color")
        self.assertEqual(attr.variation_type, "primary")

        # 2. Add Attribute Value
        resp = self.client.post(f"/admin/attributes/{attr.id}/values", data={
            "value": "Terracotta"
        })
        self.assertEqual(resp.status_code, 200) # Re-renders values list
        
        val = AttributeValue.query.filter_by(attribute_id=attr.id, value="Terracotta").first()
        self.assertIsNotNone(val)
        self.assertEqual(val.value, "Terracotta")

        # 3. Edit Attribute Value
        resp = self.client.post(f"/admin/attributes/values/{val.id}/edit", data={
            "value": "Oatmeal"
        })
        self.assertEqual(resp.status_code, 302)
        
        db_sql.session.refresh(val)
        self.assertEqual(val.value, "Oatmeal")

        # 4. Delete Value (Cascade check)
        prod = Product(id=str(uuid.uuid4()), name="Vase", slug="vase", sku="KD-V-001", price=999)
        link = ProductAttributeValue(id=str(uuid.uuid4()), product_id=prod.id, attribute_value_id=val.id)
        db_sql.session.add_all([prod, link])
        db_sql.session.commit()

        prod_id = prod.id
        link_id = link.id
        val_id = val.id

        resp = self.client.post(f"/admin/attributes/values/{val_id}/delete", data={
            "attribute_id": attr.id
        })
        self.assertEqual(resp.status_code, 302)

        # Verify value is deleted
        deleted_val = db_sql.session.get(AttributeValue, val_id)
        self.assertIsNone(deleted_val)

        # Verify association link is deleted (cascade)
        deleted_link = db_sql.session.get(ProductAttributeValue, link_id)
        self.assertIsNone(deleted_link)

    def test_simple_product_crud(self):
        # 1. Create Product
        resp = self.client.post("/admin/products/new", data={
            "name": "Street Lamp",
            "slug": "street-lamp",
            "sku": "KD-SL-001",
            "type": "simple",
            "price": "1799",
            "sale_price": "",
            "stock_quantity": "50",
            "stock_status": "in_stock",
            "is_active": "on"
        })
        self.assertEqual(resp.status_code, 302)

        prod = Product.query.filter_by(slug="street-lamp").first()
        self.assertIsNotNone(prod)
        self.assertEqual(prod.name, "Street Lamp")
        self.assertEqual(float(prod.price), 1799.0)
        self.assertEqual(prod.stock_quantity, 50)
        self.assertEqual(prod.type, "simple")

        # 2. Edit Product
        resp = self.client.post(f"/admin/products/{prod.id}/edit", data={
            "name": "Street Lamp Deluxe",
            "slug": "street-lamp-deluxe",
            "sku": "KD-SL-001",
            "type": "simple",
            "price": "1999",
            "sale_price": "1699",
            "stock_quantity": "30",
            "stock_status": "in_stock",
            "is_active": "on"
        })
        self.assertEqual(resp.status_code, 302)

        db_sql.session.refresh(prod)
        self.assertEqual(prod.name, "Street Lamp Deluxe")
        self.assertEqual(float(prod.price), 1999.0)
        self.assertEqual(float(prod.sale_price), 1699.0)
        self.assertEqual(prod.stock_quantity, 30)

        # 3. Soft Delete Product
        resp = self.client.post(f"/admin/products/{prod.id}/delete")
        self.assertEqual(resp.status_code, 302)

        db_sql.session.refresh(prod)
        self.assertEqual(prod.is_active, 0) # Inactive soft delete

    def test_variable_product_and_variations(self):
        # Create Color & Size attributes and values for testing
        attr_color = Attribute(id=str(uuid.uuid4()), name="Color", slug="color", variation_type="primary")
        attr_size = Attribute(id=str(uuid.uuid4()), name="Size", slug="size", variation_type="secondary")
        db_sql.session.add_all([attr_color, attr_size])
        db_sql.session.commit()

        val_red = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr_color.id, value="Red")
        val_blue = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr_color.id, value="Blue")
        val_small = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr_size.id, value="Small")
        val_large = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr_size.id, value="Large")
        db_sql.session.add_all([val_red, val_blue, val_small, val_large])
        db_sql.session.commit()

        # 1. Create Variable Product with attribute links
        resp = self.client.post("/admin/products/new", data={
            "name": "Ceramic Table Lamp",
            "slug": "ceramic-table-lamp",
            "sku": "KD-CTL-001",
            "type": "variable",
            "price": "2099",
            "stock_quantity": "80",
            "stock_status": "in_stock",
            "is_active": "on",
            "attribute_ids": [attr_color.id, attr_size.id],
            "attribute_value_ids": [val_red.id, val_blue.id, val_small.id, val_large.id]
        })
        self.assertEqual(resp.status_code, 302)

        prod = Product.query.filter_by(slug="ceramic-table-lamp").first()
        self.assertIsNotNone(prod)
        self.assertEqual(prod.type, "variable")

        # Verify that 4 variations were generated automatically (Red/Small, Red/Large, Blue/Small, Blue/Large)
        variations = ProductVariation.query.filter_by(product_id=prod.id).all()
        self.assertEqual(len(variations), 4)

        # Verify variation links are present
        v0 = variations[0]
        links = VariationAttributeValue.query.filter_by(variation_id=v0.id).all()
        self.assertEqual(len(links), 2) # One for color, one for size

        # 2. Bulk Update Variations
        bulk_data = {}
        for v in variations:
            bulk_data[f"sku_{v.id}"] = f"KD-LAMP-{v.id[:6].upper()}"
            bulk_data[f"price_{v.id}"] = "2499"
            bulk_data[f"stock_{v.id}"] = "15"
            bulk_data[f"name_{v.id}"] = "Textured Ceramic Lamp"
        
        resp = self.client.post(f"/admin/products/{prod.id}/variations/bulk_update", data=bulk_data)
        self.assertEqual(resp.status_code, 302)

        # Refresh and verify bulk updates
        db_sql.session.refresh(v0)
        self.assertEqual(float(v0.price), 2499.0)
        self.assertEqual(v0.stock_quantity, 15)
        self.assertEqual(v0.stock_status, "in_stock")
        self.assertEqual(v0.name, "Textured Ceramic Lamp")

        # 3. Product Type Change Edge Case: Variable -> Simple
        # This should delete all associated variations
        resp = self.client.post(f"/admin/products/{prod.id}/edit", data={
            "name": "Ceramic Table Lamp Simple",
            "slug": "ceramic-table-lamp",
            "sku": "KD-CTL-001",
            "type": "simple",
            "price": "2099",
            "stock_quantity": "80",
            "stock_status": "in_stock",
            "is_active": "on"
        })
        self.assertEqual(resp.status_code, 302)
        
        db_sql.session.refresh(prod)
        self.assertEqual(prod.type, "simple")

        # Verify variations are deleted
        deleted_variations_count = ProductVariation.query.filter_by(product_id=prod.id).count()
        self.assertEqual(deleted_variations_count, 0)

    def test_category_edge_cases(self):
        # 1. Duplicate category slug (IntegrityError check)
        resp1 = self.client.post("/admin/categories/new", data={
            "name": "Table Decor",
            "slug": "table-decor",
        })
        self.assertEqual(resp1.status_code, 302)
        
        resp2 = self.client.post("/admin/categories/new", data={
            "name": "Another Table Decor",
            "slug": "table-decor",
        })
        self.assertEqual(resp2.status_code, 200) # Form page with error flashed
        
        cat_count = Category.query.filter_by(slug="table-decor").count()
        self.assertEqual(cat_count, 1)

        # 2. Validation: Empty category name
        resp3 = self.client.post("/admin/categories/new", data={
            "name": "   ",
            "slug": "some-slug"
        })
        self.assertEqual(resp3.status_code, 200)

    def test_brand_edge_cases(self):
        # 1. Duplicate Brand Slug
        resp1 = self.client.post("/admin/brands/new", data={
            "name": "Brand A",
            "slug": "brand-a"
        })
        self.assertEqual(resp1.status_code, 302)

        resp2 = self.client.post("/admin/brands/new", data={
            "name": "Brand B",
            "slug": "brand-a"
        })
        self.assertEqual(resp2.status_code, 200)
        
        # 2. Validation: Blank Brand name
        resp3 = self.client.post("/admin/brands/new", data={
            "name": "",
            "slug": "brand-c"
        })
        self.assertEqual(resp3.status_code, 200)

    def test_attribute_edge_cases(self):
        # Create an attribute
        resp1 = self.client.post("/admin/attributes/new", data={
            "name": "Material",
            "slug": "material",
            "variation_type": "primary"
        })
        self.assertEqual(resp1.status_code, 302)
        attr = Attribute.query.filter_by(slug="material").first()
        self.assertIsNotNone(attr)

        # 1. Duplicate Attribute Slug
        resp2 = self.client.post("/admin/attributes/new", data={
            "name": "Material Duplicate",
            "slug": "material",
            "variation_type": "secondary"
        })
        self.assertEqual(resp2.status_code, 200)

        # Add some values to bulk update
        val1 = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr.id, value="Wood")
        val2 = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr.id, value="Metal")
        db_sql.session.add_all([val1, val2])
        db_sql.session.commit()

        # 2. Bulk update attribute values
        resp3 = self.client.post(f"/admin/attributes/{attr.id}/values/bulk_update", data={
            f"value_{val1.id}": "Solid Wood",
            f"value_{val2.id}": "Polished Metal"
        })
        self.assertEqual(resp3.status_code, 302)

        db_sql.session.refresh(val1)
        db_sql.session.refresh(val2)
        self.assertEqual(val1.value, "Solid Wood")
        self.assertEqual(val2.value, "Polished Metal")

        # 3. Bulk update skipping empty
        resp4 = self.client.post(f"/admin/attributes/{attr.id}/values/bulk_update", data={
            f"value_{val1.id}": "",
            f"value_{val2.id}": "Brushed Brass"
        })
        self.assertEqual(resp4.status_code, 302)
        db_sql.session.refresh(val1)
        db_sql.session.refresh(val2)
        self.assertEqual(val1.value, "Solid Wood")
        self.assertEqual(val2.value, "Brushed Brass")

    def test_product_edge_cases(self):
        # 1. Duplicate SKU check
        prod1 = Product(id=str(uuid.uuid4()), name="Product 1", slug="product-1", sku="KD-DUPLICATE-SKU", price=100)
        db_sql.session.add(prod1)
        db_sql.session.commit()

        resp = self.client.post("/admin/products/new", data={
            "name": "Product 2",
            "slug": "product-2",
            "sku": "KD-DUPLICATE-SKU",
            "type": "simple",
            "price": "200"
        })
        self.assertEqual(resp.status_code, 200)

        # 2. Duplicate slug check (should auto-generate unique slug using get_unique_slug)
        resp2 = self.client.post("/admin/products/new", data={
            "name": "Product 1",
            "sku": "KD-UNIQUE-SKU-2",
            "type": "simple",
            "price": "300"
        })
        self.assertEqual(resp2.status_code, 302)
        prod2 = Product.query.filter_by(sku="KD-UNIQUE-SKU-2").first()
        self.assertIsNotNone(prod2)
        self.assertNotEqual(prod2.slug, "product-1")
        self.assertTrue(prod2.slug.startswith("product-1"))

        # 3. Invalid pricing formats
        resp3 = self.client.post("/admin/products/new", data={
            "name": "Product Invalid Price",
            "sku": "KD-INVALID-PRICE",
            "type": "simple",
            "price": "abc"
        })
        self.assertEqual(resp3.status_code, 200)

    def test_variation_edge_cases(self):
        # Create a variable product
        attr = Attribute(id=str(uuid.uuid4()), name="Type", slug="type", variation_type="primary")
        db_sql.session.add(attr)
        db_sql.session.commit()
        val_a = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr.id, value="Option A")
        val_b = AttributeValue(id=str(uuid.uuid4()), attribute_id=attr.id, value="Option B")
        db_sql.session.add_all([val_a, val_b])
        db_sql.session.commit()

        prod = Product(id=str(uuid.uuid4()), name="Parent Product", slug="parent-product", sku="KD-PARENT", type="variable")
        p_attr = ProductAttribute(id=str(uuid.uuid4()), product_id=prod.id, attribute_id=attr.id)
        p_val_a = ProductAttributeValue(id=str(uuid.uuid4()), product_id=prod.id, attribute_value_id=val_a.id)
        p_val_b = ProductAttributeValue(id=str(uuid.uuid4()), product_id=prod.id, attribute_value_id=val_b.id)
        db_sql.session.add_all([prod, p_attr, p_val_a, p_val_b])
        db_sql.session.commit()

        generate_variations(prod.id)
        variations = ProductVariation.query.filter_by(product_id=prod.id).all()
        self.assertEqual(len(variations), 2)

        v1 = variations[0]
        v1_id = v1.id

        # Deleting variation
        resp2 = self.client.post(f"/admin/variations/{v1_id}/delete", data={
            "product_id": prod.id
        })
        self.assertEqual(resp2.status_code, 302)
        deleted_v1 = db_sql.session.get(ProductVariation, v1_id)
        self.assertIsNone(deleted_v1)

    def test_admin_listing_pages(self):
        # Request key dashboard / list pages to verify correct query compilation and template rendering
        pages = [
            "/admin",
            "/admin/products",
            "/admin/categories",
            "/admin/brands",
            "/admin/attributes",
            "/admin/orders",
            "/admin/customers",
            "/admin/subscribers"
        ]
        for path in pages:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"Failed to load path: {path}")


if __name__ == "__main__":
    unittest.main()
