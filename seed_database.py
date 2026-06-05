import os
import sys
import uuid
import bcrypt
from decimal import Decimal

sys.path.append(os.path.abspath('.'))

from app import create_app
from extensions import db_sql
from models import (
    Category, Brand, Product, Media, ProductImage, Attribute, AttributeValue,
    ProductAttribute, ProductAttributeValue, ProductVariation,
    VariationAttributeValue, VariationImage, ProductReview, User, UserAddress
)

# Initialize application context
app = create_app()

def seed_db():
    print("=== STARTING DATABASE RE-SEED WITH WEBP IMAGES ===")
    
    with app.app_context():
        print("Terminating other database connections...")
        try:
            db_sql.session.execute(db_sql.text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid();"
            ))
            db_sql.session.commit()
            print("Other database connections terminated.")
        except Exception as e:
            db_sql.session.rollback()
            print(f"Warning: could not terminate other connections: {e}")


        print("Dropping all tables to clean database...")
        try:
            db_sql.reflect()
            db_sql.drop_all()
            print("Dropped existing tables successfully.")
        except Exception as e:
            print(f"Error dropping tables: {e}")
            raise e

            
        import db
        db.migrate()
        print("Successfully created all database tables and triggers fresh.")
        
        # 1. Seed Users
        print("Seeding users...")
        pwd_hash_admin = bcrypt.hashpw(b"adminpassword", bcrypt.gensalt()).decode("utf-8")
        pwd_hash_user = bcrypt.hashpw(b"userpassword", bcrypt.gensalt()).decode("utf-8")
        
        admin_id = str(uuid.uuid4())
        admin_user = User(
            id=admin_id,
            first_name="Admin",
            last_name="Owner",
            email="admin@example.com",
            password_hash=pwd_hash_admin,
            role="admin"
        )
        
        user_id = str(uuid.uuid4())
        customer_user = User(
            id=user_id,
            first_name="Aamir",
            last_name="Khan",
            email="user@example.com",
            password_hash=pwd_hash_user,
            role="customer"
        )
        
        db_sql.session.add(admin_user)
        db_sql.session.add(customer_user)
        
        # Seed customer user address
        customer_addr = UserAddress(
            id=str(uuid.uuid4()),
            user_id=user_id,
            label="Home",
            first_name="Aamir",
            last_name="Khan",
            phone="9876543210",
            address_line1="123 Elegant Decor Lane",
            address_line2="Near Creative Studio",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            country="India",
            is_default=1
        )
        db_sql.session.add(customer_addr)
        
        # 2. Seed Brand
        print("Seeding brands...")
        brand = Brand(
            id=str(uuid.uuid4()),
            name="Khushi Decors Elite",
            slug="khushi-decors-elite"
        )
        db_sql.session.add(brand)
        db_sql.session.flush()
        
        # 3. Seed Categories & Subcategories
        print("Seeding categories and subcategories...")
        categories_data = [
            {
                "name": "Led mirrors",
                "slug": "led-mirrors",
                "image_url": "/uploads/04c03625ec68.webp",
                "subcats": [
                    "Designer LED Mirrors",
                    "Bathroom LED Mirrors",
                    "Dressing LED Mirrors",
                    "Touch Sensor LED Mirrors",
                    "Backlit LED Mirrors"
                ]
            },
            {
                "name": "Decorative Mirrors",
                "slug": "decorative-mirrors",
                "image_url": "/uploads/a3778c1cf7c1.webp",
                "subcats": [
                    "Plain Mirrors",
                    "Tukdi Mirrors",
                    "Fancy Mirrors",
                    "Dressing Mirrors",
                    "Wall Mirrors"
                ]
            },
            {
                "name": "Wall Art",
                "slug": "wall-art",
                "image_url": "/uploads/6869de5d347e.webp",
                "subcats": [
                    "Mirror Wall Art",
                    "MDF Wall Art",
                    "LED Wall Art",
                    "Decorative Wall Panels"
                ]
            },
            {
                "name": "Home Decor Items",
                "slug": "home-decor-items",
                "image_url": "/uploads/1909117adb92.webp",
                "subcats": [
                    "Wooden Items",
                    "Key Holders",
                    "Sofa Arm Trays",
                    "Foot Rests",
                    "Wine Racks",
                    "Shelves",
                    "Glass Shelves",
                    "Wooden Shelves",
                    "Puzzles solving miniature MDF models",
                    "Puzzles solving miniature acrylic models"
                ]
            },
            {
                "name": "Table & Glass Decor",
                "slug": "table-glass-decor",
                "image_url": "/uploads/f7deecc25953.avif",
                "subcats": [
                    "Glass Highlighters",
                    "Table Tops",
                    "Glass Decor Items"
                ]
            },
            {
                "name": "Name Plates",
                "slug": "name-plates",
                "image_url": "/uploads/41b09de02574.webp",
                "subcats": [
                    "MDF Name Plates",
                    "Glass Name Plates",
                    "LED Name Plates",
                    "Acrylic name plates"
                ]
            },
            {
                "name": "Paintings and Art",
                "slug": "paintings-and-art",
                "image_url": "/uploads/0869520fdfe8.jpg",
                "subcats": [
                    "Piece Paintings",
                    "Modern Wall Paintings",
                    "Decorative Art Frames"
                ]
            },
            {
                "name": "Wall Clocks",
                "slug": "wall-clocks",
                "image_url": "/uploads/a3ae4e39121d.jpg",
                "subcats": [
                    "MDF premium wall clocks",
                    "Antique wall clocks",
                    "Acrylic wall clocks",
                    "Glass wall clocks",
                    "Led wall clocks"
                ]
            }
        ]
        
        cat_map = {}
        for c_info in categories_data:
            parent_cat = Category(
                id=str(uuid.uuid4()),
                name=c_info["name"],
                slug=c_info["slug"],
                image_url=c_info["image_url"]
            )
            db_sql.session.add(parent_cat)
            db_sql.session.flush()
            
            for sub_name in c_info["subcats"]:
                sub_slug = sub_name.lower().replace(" ", "-").replace("&", "and").replace("(", "").replace(")", "")
                sub_cat = Category(
                    id=str(uuid.uuid4()),
                    parent_id=parent_cat.id,
                    name=sub_name,
                    slug=sub_slug
                )
                db_sql.session.add(sub_cat)
                cat_map[sub_name] = sub_cat
                
        db_sql.session.flush()
        
        # 4. Seed Variation Attributes
        print("Seeding variation attributes...")
        shape_attr = Attribute(
            id=str(uuid.uuid4()),
            name="Shape",
            slug="shape",
            variation_type="primary"
        )
        size_attr = Attribute(
            id=str(uuid.uuid4()),
            name="Size",
            slug="size",
            variation_type="secondary"
        )
        db_sql.session.add(shape_attr)
        db_sql.session.add(size_attr)
        db_sql.session.flush()
        
        # Attribute Values
        shape_vals = {}
        shapes_list = ["Oval", "Round", "Triangular", "Square", "Rectangular"]
        shape_swatch_urls = {
            "Oval": "/static/images/led_mirror_oval/oval_1.webp",
            "Round": "/static/images/led_mirror_round/round_1.webp",
            "Triangular": "/static/images/led_mirror_triangular/traingular_1.webp",
            "Square": "/static/images/led_mirror_square/square_1.webp",
            "Rectangular": "/static/images/led_mirror_rectangular/rect_1.webp"
        }
        
        for sname in shapes_list:
            val_id = str(uuid.uuid4())
            val = AttributeValue(
                id=val_id,
                attribute_id=shape_attr.id,
                value=sname,
                image_url=shape_swatch_urls[sname]
            )
            db_sql.session.add(val)
            shape_vals[sname] = val
            
        size_vals = {}
        for sname in ["18x18", "21x21", "24x24"]:
            val_id = str(uuid.uuid4())
            val = AttributeValue(
                id=val_id,
                attribute_id=size_attr.id,
                value=sname
            )
            db_sql.session.add(val)
            size_vals[sname] = val
            
        db_sql.session.flush()
        
        # 5. Gather Media lists from folder structures
        # Helper function to cache and seed media
        media_cache = {}
        def get_media_id(url, alt=""):
            if url in media_cache:
                return media_cache[url]
            m_id = str(uuid.uuid4())
            m = Media(id=m_id, file_url=url, alt_text=alt)
            db_sql.session.add(m)
            media_cache[url] = m_id
            return m_id

        # LED Mirror Shape Image Pools
        oval_images = [f"/static/images/led_mirror_oval/oval_{i}.webp" for i in range(1, 8)]
        round_images = [f"/static/images/led_mirror_round/round_{i}.webp" for i in range(1, 11)]
        tri_images = [f"/static/images/led_mirror_triangular/traingular_{i}.webp" for i in range(1, 9)]
        square_images = [f"/static/images/led_mirror_square/square_{i}.webp" for i in range(1, 11)]
        rect_images = [f"/static/images/led_mirror_rectangular/rect_{i}.webp" for i in range(1, 11)]

        # 6. Seed Variable Product: "Premium Designer LED Mirror"
        print("Seeding Variable LED Mirror Product...")
        product_id = str(uuid.uuid4())
        var_product = Product(
            id=product_id,
            category_id=cat_map["Designer LED Mirrors"].id,
            brand_id=brand.id,
            name="Premium Designer LED Mirror",
            slug="premium-designer-led-mirror",
            sku="PREM-LED-MR",
            type="variable",
            short_description="Exquisite designer LED mirror beautifully handcrafted in India. Fully customizable with multiple premium shapes and sizing options.",
            description="""<h3>Timeless Design & Radiant Glow</h3>
<p>Transform your interior spaces into a luxury boutique sanctuary with the Premium Designer LED Mirror. Hand-structured by master artisans, this backlit styling masterpiece delivers perfectly diffused illumination and clean reflections.</p>
<p>Each unit features highly durable copper-free backing, soft warm/cool glow settings, and a fully polished sleek edge designed to integrate beautifully with master bathrooms, dresser alcoves, or architectural corridors.</p>
<h4>Styling Guidelines</h4>
<p>For the ultimate styling impact, pair this backlit statement mirror with high-visibility entryway styling tables, brass fixtures, and soft warm spotlights to highlight the soft textured halos.</p>""",
            price=Decimal("3299.00"), # Base price
            stock_quantity=80,
            stock_status="in_stock",
            is_featured=1,
            is_active=1
        )
        db_sql.session.add(var_product)
        
        # Link Product Attributes
        pa1 = ProductAttribute(id=str(uuid.uuid4()), product_id=product_id, attribute_id=shape_attr.id, display_order=0)
        pa2 = ProductAttribute(id=str(uuid.uuid4()), product_id=product_id, attribute_id=size_attr.id, display_order=1)
        db_sql.session.add(pa1)
        db_sql.session.add(pa2)
        
        # Link Product Attribute Values
        for v in shape_vals.values():
            db_sql.session.add(ProductAttributeValue(id=str(uuid.uuid4()), product_id=product_id, attribute_value_id=v.id))
        for v in size_vals.values():
            db_sql.session.add(ProductAttributeValue(id=str(uuid.uuid4()), product_id=product_id, attribute_value_id=v.id))
            
        # Add Product Gallery Images (Parent defaults)
        parent_img_urls = [
            "/static/images/led_mirror_round/round_1.webp",
            "/static/images/led_mirror_oval/oval_1.webp",
            "/static/images/led_mirror_rectangular/rect_1.webp",
            "/static/images/led_mirror_square/square_1.webp",
            "/static/images/led_mirror_triangular/traingular_1.webp"
        ]
        for idx, url in enumerate(parent_img_urls):
            m_id = get_media_id(url, f"Premium Designer Mirror Default View {idx+1}")
            pi = ProductImage(
                id=str(uuid.uuid4()),
                product_id=product_id,
                media_id=m_id,
                is_primary=1 if idx == 0 else 0,
                display_order=idx
            )
            db_sql.session.add(pi)
            
        db_sql.session.flush()
        
        # 7. Create 15 Variations (5 shapes * 3 sizes)
        print("Generating 15 variations...")
        shapes_matrix = ["Oval", "Round", "Triangular", "Square", "Rectangular"]
        sizes_matrix = [
            {"size": "18x18", "price": 3999.0, "sale_price": 3299.0, "sku_suffix": "18"},
            {"size": "21x21", "price": 4999.0, "sale_price": 4299.0, "sku_suffix": "21"},
            {"size": "24x24", "price": 5999.0, "sale_price": 5299.0, "sku_suffix": "24"}
        ]
        
        for sname in shapes_matrix:
            for sz_item in sizes_matrix:
                v_id = str(uuid.uuid4())
                v_sku = f"LED-{sname[:4].upper()}-{sz_item['sku_suffix']}"
                v_name = f"Premium Designer LED Mirror – {sname}, {sz_item['size']}"
                
                variation = ProductVariation(
                    id=v_id,
                    product_id=product_id,
                    sku=v_sku,
                    price=Decimal(str(sz_item["price"])),
                    sale_price=Decimal(str(sz_item["sale_price"])),
                    stock_quantity=15,
                    stock_status="in_stock",
                    name=v_name,
                    short_description=f"Specialist {sname} LED mirror refined in {sz_item['size']} size.",
                    description=f"<p>Handcrafted premium {sname} mirror option measured precisely at {sz_item['size']} inches. Features premium backlit glow borders, double polished silver backing, and anti-fog demisting technology.</p>"
                )
                db_sql.session.add(variation)
                
                # Map Variation Attribute values
                db_sql.session.add(VariationAttributeValue(id=str(uuid.uuid4()), variation_id=v_id, attribute_value_id=shape_vals[sname].id))
                db_sql.session.add(VariationAttributeValue(id=str(uuid.uuid4()), variation_id=v_id, attribute_value_id=size_vals[sz_item["size"]].id))
                
                # Custom Variation-Specific images slice (grab up to 3)
                img_pool = []
                if sname == "Oval": img_pool = oval_images
                elif sname == "Round": img_pool = round_images
                elif sname == "Triangular": img_pool = tri_images
                elif sname == "Square": img_pool = square_images
                elif sname == "Rectangular": img_pool = rect_images
                
                if img_pool:
                    var_slice = img_pool[:3]
                    for v_idx, img_url in enumerate(var_slice):
                        v_med_id = get_media_id(img_url, f"{v_name} Thumbnail {v_idx+1}")
                        vi = VariationImage(
                            id=str(uuid.uuid4()),
                            variation_id=v_id,
                            media_id=v_med_id,
                            is_primary=1 if v_idx == 0 else 0,
                            display_order=v_idx
                        )
                        db_sql.session.add(vi)
                        
        db_sql.session.flush()

        # 8. Seed Simple LED Mirrors (Bathroom, Dressing, Touch Sensor, Backlit)
        print("Seeding Simple LED Mirrors...")
        simple_mirrors_data = [
            {
                "subcat": "Bathroom LED Mirrors",
                "name": "Luxury Backlit Bathroom LED Mirror",
                "slug": "luxury-backlit-bathroom-led-mirror",
                "sku": "LED-BATH-BK",
                "price": 3800.0,
                "sale_price": 3199.0,
                "desc": "Sleek rectangular bathroom LED mirror with frosted border accents, dual touch light triggers, and integrated demister.",
                "images": ["/static/images/led_mirror_rectangular/rect_4.webp", "/static/images/led_mirror_rectangular/rect_5.webp"]
            },
            {
                "subcat": "Dressing LED Mirrors",
                "name": "Arched Dressing Vanity LED Mirror",
                "slug": "arched-dressing-vanity-led-mirror",
                "sku": "LED-DRESS-AR",
                "price": 6800.0,
                "sale_price": 5999.0,
                "desc": "Gorgeous tall arched vanity dressing mirror featuring gold frame accents and high density warm ambient halo backlights.",
                "images": ["/static/images/led_mirror_oval/oval_4.webp", "/static/images/led_mirror_oval/oval_5.webp"]
            },
            {
                "subcat": "Touch Sensor LED Mirrors",
                "name": "Horizon Dual-Touch Intelligent Mirror",
                "slug": "horizon-dual-touch-intelligent-mirror",
                "sku": "LED-TOUCH-HZ",
                "price": 4900.0,
                "sale_price": 4350.0,
                "desc": "Smart circular touch sensor mirror supporting multi-color dimmable backlighting and automated memory light recall.",
                "images": ["/static/images/led_mirror_round/round_4.webp", "/static/images/led_mirror_round/round_5.webp"]
            },
            {
                "subcat": "Backlit LED Mirrors",
                "name": "Solitaire Ambient Square Glow Mirror",
                "slug": "solitaire-ambient-square-glow-mirror",
                "sku": "LED-GLOW-SQ",
                "price": 5200.0,
                "sale_price": 4500.0,
                "desc": "Minimalist square wall mirror lined with elegant continuous neon backing strip for floating style wall glow.",
                "images": ["/static/images/led_mirror_square/square_4.webp", "/static/images/led_mirror_square/square_5.webp"]
            }
        ]

        for s_item in simple_mirrors_data:
            p_id = str(uuid.uuid4())
            prod = Product(
                id=p_id,
                category_id=cat_map[s_item["subcat"]].id,
                brand_id=brand.id,
                name=s_item["name"],
                slug=s_item["slug"],
                sku=s_item["sku"],
                type="simple",
                short_description=s_item["desc"],
                description=f"<h3>Premium Craftsmanship</h3><p>{s_item['desc']}</p><p>Built by master generational artisans with highly durable copper-free glass, anti-shatter film layers, and premium rustproof aluminum styling backboards.</p>",
                price=Decimal(str(s_item["price"])),
                sale_price=Decimal(str(s_item["sale_price"])) if s_item.get("sale_price") else None,
                stock_quantity=20,
                stock_status="in_stock",
                is_featured=0,
                is_active=1
            )
            db_sql.session.add(prod)
            for idx, img_url in enumerate(s_item["images"]):
                m_id = get_media_id(img_url, f"{s_item['name']} View {idx+1}")
                db_sql.session.add(ProductImage(
                    id=str(uuid.uuid4()),
                    product_id=p_id,
                    media_id=m_id,
                    is_primary=1 if idx == 0 else 0,
                    display_order=idx
                ))
        db_sql.session.flush()

        # 9. Seed Clocks (Statement Clocks)
        print("Seeding Statement Clocks...")
        clocks_data = [
            {"name": "Nordic Solid Oak Concrete Clock", "subcat": "MDF premium wall clocks", "sku": "CLK-OAK-01", "img": "CLOCK1.webp", "price": 1800.0, "sale_price": 1499.0, "desc": "Contemporary silent wall clock crafted in structured concrete dial with polished solid oak hour hands."},
            {"name": "Pastel Matte Modern Silent Clock", "subcat": "Acrylic wall clocks", "sku": "CLK-PST-02", "img": "CLOCK2.webp", "price": 1350.0, "sale_price": 1150.0, "desc": "Minimalist silent sweep wall clock finished in gorgeous matte pastel shades and sleek white markings."},
            {"name": "Artisan Handcrafted Brass Station Clock", "subcat": "Antique wall clocks", "sku": "CLK-BRS-03", "img": "CLOCK3.webp", "price": 4200.0, "sale_price": 3600.0, "desc": "Ornate Rajasthani hand-forged antique brass dial clock with dual-sided wall mount iron brackets."},
            {"name": "Geometric Hexagon Matte Wall Clock", "subcat": "MDF premium wall clocks", "sku": "CLK-HEX-04", "img": "CLOCK4.webp", "price": 2100.0, "sale_price": 1850.0, "desc": "Statement geometric design wall clock with contrasting metallic hands, ideal for executive studies."}
        ]
        for idx, item in enumerate(clocks_data):
            p_id = str(uuid.uuid4())
            slug = item["name"].lower().replace(" ", "-")
            img_url = f"/static/images/clock/{item['img']}"
            prod = Product(
                id=p_id,
                category_id=cat_map[item["subcat"]].id,
                brand_id=brand.id,
                name=item["name"],
                slug=slug,
                sku=item["sku"],
                type="simple",
                short_description=item["desc"],
                description=f"<h3>Premium Architectural Accent</h3><p>{item['desc']}</p><p>Requires 1 x AA Battery (not included). Handcrafted in India with silent clock mechanisms, avoiding any ticking noise, making it suitable for quiet bedrooms and home libraries.</p>",
                price=Decimal(str(item["price"])),
                sale_price=Decimal(str(item["sale_price"])) if item.get("sale_price") else None,
                stock_quantity=25,
                stock_status="in_stock",
                is_featured=1 if idx == 0 else 0,
                is_active=1
            )
            db_sql.session.add(prod)
            m_id = get_media_id(img_url, item["name"])
            db_sql.session.add(ProductImage(
                id=str(uuid.uuid4()),
                product_id=p_id,
                media_id=m_id,
                is_primary=1,
                display_order=0
            ))
        db_sql.session.flush()

        # 10. Seed Lamps (Designer Lamps)
        print("Seeding Designer Lamps...")
        lamps_data = [
            {"name": "Ceramic Matte Ribbed Table Lamp", "sku": "LMP-CRM-01", "img": "LAMP1.webp", "price": 2499.0, "sale_price": 1999.0, "desc": "Beautiful ribbed ceramic bedside table lamp in soft terracotta finish with linen drum shade."},
            {"name": "Industrial Brass Dome Desk Lamp", "sku": "LMP-IND-02", "img": "LAMP2.webp", "price": 3200.0, "sale_price": 2750.0, "desc": "Adjustable brass desk lamp with heavy duty base and raw dome lighting shade perfect for workspace study tables."},
            {"name": "Glass Globe Brass Pendant Lamp", "sku": "LMP-GLB-03", "img": "LAMP3.webp", "price": 4500.0, "sale_price": 3999.0, "desc": "Pendant light fixture showcasing a handblown frosted glass globe on solid brushed brass rod fittings."},
            {"name": "Woven Rattan Organic Floor Lamp", "sku": "LMP-RAT-04", "img": "LAMP4.webp", "price": 5400.0, "sale_price": 4650.0, "desc": "Tall tripod standing floor lamp wrapped inside a gorgeous hand-woven organic rattan mesh shade."},
            {"name": "Brushed Chrome Arch Floor Lamp", "sku": "LMP-ARC-05", "img": "LAMP5.webp", "price": 6800.0, "sale_price": 5899.0, "desc": "Sleek modern curved arch floor lamp in polished steel plating designed to hang elegantly over sofas."},
            {"name": "Smart Ambient Glow Bedside Cube", "sku": "LMP-CUB-06", "img": "LAMP6.webp", "price": 1900.0, "sale_price": 1499.0, "desc": "Compact frosted acrylic cube bedside ambient lamp with wireless remote supporting multi-color dimmable glow."}
        ]
        for idx, item in enumerate(lamps_data):
            p_id = str(uuid.uuid4())
            slug = item["name"].lower().replace(" ", "-")
            img_url = f"/static/images/lamp/{item['img']}"
            prod = Product(
                id=p_id,
                category_id=cat_map["Glass Decor Items"].id,
                brand_id=brand.id,
                name=item["name"],
                slug=slug,
                sku=item["sku"],
                type="simple",
                short_description=item["desc"],
                description=f"<h3>Premium Lighting Experience</h3><p>{item['desc']}</p><p>Includes a complimentary warm-glowing E27 LED bulb. Fully tested and wired for standard Indian electrical outlets with inline toggle switches and high-grade safety shielding cables.</p>",
                price=Decimal(str(item["price"])),
                sale_price=Decimal(str(item["sale_price"])) if item.get("sale_price") else None,
                stock_quantity=30,
                stock_status="in_stock",
                is_featured=1 if idx == 0 else 0,
                is_active=1
            )
            db_sql.session.add(prod)
            m_id = get_media_id(img_url, item["name"])
            db_sql.session.add(ProductImage(
                id=str(uuid.uuid4()),
                product_id=p_id,
                media_id=m_id,
                is_primary=1,
                display_order=0
            ))
        db_sql.session.flush()

        # 11. Seed Vases (Vases & Vessels)
        print("Seeding Vases & Vessels...")
        vases_data = [
            {"name": "Matte White Textured Ceramic Vase", "sku": "VAS-CRM-01", "img": "VASE1.webp", "price": 1200.0, "sale_price": 950.0, "desc": "Artistic dry-brushed finish ceramic vase designed for styling dry pampas grass decor overlays."},
            {"name": "Ribbed Amber Fluted Glass Vessel", "sku": "VAS-GLS-02", "img": "VASE2.webp", "price": 980.0, "sale_price": 799.0, "desc": "Gorgeous fluted glass vase in rich warm amber hue with beveled rim, ideal for fresh flower cuttings."},
            {"name": "Terracotta Earthen Ribbed Urn", "sku": "VAS-ERN-03", "img": "VASE3.webp", "price": 1650.0, "sale_price": 1350.0, "desc": "Traditional ribbed clay storage urn styled vessel showcasing raw textured surfaces and natural terracotta tones."},
            {"name": "Minimalist Porcelain Bud Vase Set", "sku": "VAS-BUD-04", "img": "VASE4.webp", "price": 1400.0, "sale_price": 1199.0, "desc": "Set of three miniature organic-shaped porcelain bud vases finished in smooth satin glaze."},
            {"name": "Textured Stone Architectural Vessel", "sku": "VAS-STN-05", "img": "VASE5.webp", "price": 2800.0, "sale_price": 2400.0, "desc": "Sculptural heavy stone vase carved with clean geometric lines, serving as a beautiful standalone styling piece."}
        ]
        for idx, item in enumerate(vases_data):
            p_id = str(uuid.uuid4())
            slug = item["name"].lower().replace(" ", "-")
            img_url = f"/static/images/vase/{item['img']}"
            prod = Product(
                id=p_id,
                category_id=cat_map["Glass Decor Items"].id,
                brand_id=brand.id,
                name=item["name"],
                slug=slug,
                sku=item["sku"],
                type="simple",
                short_description=item["desc"],
                description=f"<h3>Premium Table Styling</h3><p>{item['desc']}</p><p>Fully waterproofed interior lining ensures support for fresh stems. Clean with soft damp cloths; avoid using abrasive chemicals to preserve the textured surface finish.</p>",
                price=Decimal(str(item["price"])),
                sale_price=Decimal(str(item["sale_price"])) if item.get("sale_price") else None,
                stock_quantity=20,
                stock_status="in_stock",
                is_featured=1 if idx == 0 else 0,
                is_active=1
            )
            db_sql.session.add(prod)
            m_id = get_media_id(img_url, item["name"])
            db_sql.session.add(ProductImage(
                id=str(uuid.uuid4()),
                product_id=p_id,
                media_id=m_id,
                is_primary=1,
                display_order=0
            ))
        db_sql.session.flush()

        # 12. Seed Wall Art (MDF Wall Art & Mirror Wall Art)
        print("Seeding Wall Art...")
        wall_art_data = [
            {"name": "Tree of Life Cutout MDF Panel", "subcat": "MDF Wall Art", "sku": "ART-MDF-01", "img": "wall_deco_1.webp", "price": 1500.0, "sale_price": 1250.0, "desc": "Intricate laser-cut circular MDF panel depicting a tree silhouette finished in gorgeous matte charcoal lacquer."},
            {"name": "Celestial Gilded Sunburst Mirror", "subcat": "Mirror Wall Art", "sku": "ART-SUN-02", "img": "wall_deco_2.webp", "price": 3800.0, "sale_price": 3199.0, "desc": "Statement mirror collage surrounded by metal leaf-wrapped sunburst rays, finished in Rajasthani gold plating."},
            {"name": "Spiritual Mandala Carved Wood Panel", "subcat": "MDF Wall Art", "sku": "ART-MDL-03", "img": "wall_deco_3.webp", "price": 1900.0, "sale_price": 1600.0, "desc": "Layered MDF mandala wood cutout with beautiful floral engravings, designed for tranquil study rooms."},
            {"name": "Abstract Metal Ginkgo Leaf Board", "subcat": "MDF Wall Art", "sku": "ART-GNK-04", "img": "wall_deco_4.webp", "price": 2800.0, "sale_price": 2400.0, "desc": "Elegant 3D branching ginkgo leaf wall installation plate finished in gold and brushed sage-green highlights."},
            {"name": "Hand-painted Golden Foil Canvas", "subcat": "MDF Wall Art", "sku": "ART-CNV-05", "img": "wall_deco_5.webp", "price": 5400.0, "sale_price": 4500.0, "desc": "Large textured abstract canvas panel highlighting beautiful acrylic strokes and authentic golden foil overlays."}
        ]
        for idx, item in enumerate(wall_art_data):
            p_id = str(uuid.uuid4())
            slug = item["name"].lower().replace(" ", "-")
            img_url = f"/static/images/wall_deco/{item['img']}"
            prod = Product(
                id=p_id,
                category_id=cat_map[item["subcat"]].id,
                brand_id=brand.id,
                name=item["name"],
                slug=slug,
                sku=item["sku"],
                type="simple",
                short_description=item["desc"],
                description=f"<h3>Premium Artisanal Wall Decor</h3><p>{item['desc']}</p><p>Fully equipped with heavy duty flush-mount keyhole hangers on the back for stable wall mounting. Hand-painted or laser-cut in India, ensuring excellent tolerances and design precision.</p>",
                price=Decimal(str(item["price"])),
                sale_price=Decimal(str(item["sale_price"])) if item.get("sale_price") else None,
                stock_quantity=15,
                stock_status="in_stock",
                is_featured=1 if idx == 0 else 0,
                is_active=1
            )
            db_sql.session.add(prod)
            m_id = get_media_id(img_url, item["name"])
            db_sql.session.add(ProductImage(
                id=str(uuid.uuid4()),
                product_id=p_id,
                media_id=m_id,
                is_primary=1,
                display_order=0
            ))
        db_sql.session.flush()

        # 13. Seed Customer Reviews
        print("Seeding customer reviews...")
        reviews_data = [
            {
                "rating": 5,
                "body": "This Premium LED Mirror is absolutely gorgeous! The Oval shape option is incredibly stylish, touch sensors work flawlessly, and the lighting is perfect. Best purchase ever!"
            },
            {
                "rating": 4,
                "body": "Highly happy with the Round shape mirror option. Arrived well packaged and fits perfectly in my dressing room. The back-lighting effect adds a very cozy ambiance."
            },
            {
                "rating": 5,
                "body": "The Triangular LED mirror is a total masterpiece! Visitors in my home are wowed immediately. Exceptional build quality and sleek design borders."
            }
        ]
        for rev in reviews_data:
            review = ProductReview(
                id=str(uuid.uuid4()),
                product_id=product_id,
                user_id=customer_user.id,
                rating=rev["rating"],
                body=rev["body"],
                is_approved=1
            )
            db_sql.session.add(review)
            
        db_sql.session.commit()
        print("=== DATABASE SEEDING COMPLETED SUCCESSFULLY ===")

if __name__ == '__main__':
    seed_db()
