"""
db.py — Database management using Flask-SQLAlchemy.
Handles connection pooling and schema initialization.
"""
import os
from dotenv import load_dotenv
from extensions import db_sql

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    """Return a raw connection from the SQLAlchemy connection pool."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Set it in your .env file, e.g.:\n"
            "DATABASE_URL=postgresql://user:pass@host:5432/dbname"
        )
    return db_sql.engine.raw_connection()

def _pg(sql):
    """Convert SQLite ? placeholders to PostgreSQL %s placeholders."""
    return sql.replace("?", "%s")

def query(sql, params=None):
    """Run a query using the SQLAlchemy engine and return dict-like rows."""
    with db_sql.engine.connect() as conn:
        res = conn.exec_driver_sql(_pg(sql), tuple(params or ()))
        if res.returns_rows:
            cols = res.keys()
            return [dict(zip(cols, row)) for row in res.fetchall()]
        return []

def query_one(sql, params=None):
    """Run a query and return the first row as a dict, or None."""
    rows = query(sql, params)
    return rows[0] if rows else None

def execute(sql, params=None):
    """Execute a statement using the SQLAlchemy engine within a transaction block."""
    with db_sql.engine.begin() as conn:
        res = conn.exec_driver_sql(_pg(sql), tuple(params or ()))
        return res.rowcount

def execute_returning(sql, params=None):
    """Execute a statement and return the first row as a dict, or None."""
    with db_sql.engine.begin() as conn:
        res = conn.exec_driver_sql(_pg(sql), tuple(params or ()))
        if res.returns_rows:
            cols = res.keys()
            row = res.fetchone()
            return dict(zip(cols, row)) if row else None
        return None

def migrate():
    """Ensure all models are registered and create tables / triggers."""
    import models  # Register models with metadata
    
    # Create tables
    db_sql.create_all()
    
    # Define and create triggers for synchronization (PostgreSQL syntax)
    triggers = [
        # 1. Sync variation pricing functions & trigger
        """CREATE OR REPLACE FUNCTION trg_sync_variation_pricing_fn()
           RETURNS TRIGGER AS $$
           BEGIN
               IF (SELECT type FROM products WHERE id = NEW.product_id) <> 'variable' THEN
                   UPDATE product_variations
                      SET price = (SELECT COALESCE(price, 0) FROM products WHERE id = NEW.product_id),
                          sale_price = (SELECT sale_price FROM products WHERE id = NEW.product_id),
                          stock_quantity = (SELECT COALESCE(stock_quantity, 0) FROM products WHERE id = NEW.product_id)
                    WHERE id = NEW.id;
               ELSE
                   IF NEW.price IS NULL OR NEW.price = 0 THEN
                       UPDATE product_variations
                          SET price = (SELECT COALESCE(price, 0) FROM products WHERE id = NEW.product_id),
                              sale_price = (SELECT sale_price FROM products WHERE id = NEW.product_id)
                        WHERE id = NEW.id;
                   END IF;
                   IF NEW.stock_quantity IS NULL OR NEW.stock_quantity = 0 THEN
                       UPDATE product_variations
                          SET stock_quantity = (SELECT COALESCE(stock_quantity, 0) FROM products WHERE id = NEW.product_id)
                        WHERE id = NEW.id;
                   END IF;
               END IF;
               RETURN NEW;
           END;
           $$ LANGUAGE plpgsql;""",
           
        """DROP TRIGGER IF EXISTS trg_sync_variation_pricing ON product_variations;""",
        
        """CREATE TRIGGER trg_sync_variation_pricing
           AFTER INSERT ON product_variations
           FOR EACH ROW
           EXECUTE FUNCTION trg_sync_variation_pricing_fn();""",

        # 2. Sync variations from product changes
        """CREATE OR REPLACE FUNCTION trg_sync_variations_from_product_fn()
           RETURNS TRIGGER AS $$
           BEGIN
               IF NEW.type <> 'variable' THEN
                   UPDATE product_variations
                      SET price = COALESCE(NEW.price, 0),
                          sale_price = NEW.sale_price,
                          stock_quantity = COALESCE(NEW.stock_quantity, 0)
                    WHERE product_id = NEW.id;
               END IF;
               RETURN NEW;
           END;
           $$ LANGUAGE plpgsql;""",
           
        """DROP TRIGGER IF EXISTS trg_sync_variations_from_product ON products;""",
        
        """CREATE TRIGGER trg_sync_variations_from_product
           AFTER UPDATE OF price, sale_price, stock_quantity ON products
           FOR EACH ROW
           EXECUTE FUNCTION trg_sync_variations_from_product_fn();""",

        # 3. Set order number if missing
        """CREATE OR REPLACE FUNCTION trg_set_order_number_if_missing_fn()
           RETURNS TRIGGER AS $$
           BEGIN
               IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
                   UPDATE orders
                      SET order_number = 'ORD-' || UPPER(SUBSTRING(encode(gen_random_bytes(6), 'hex'), 1, 12))
                    WHERE id = NEW.id;
               END IF;
               RETURN NEW;
           END;
           $$ LANGUAGE plpgsql;""",
           
        """DROP TRIGGER IF EXISTS trg_set_order_number_if_missing ON orders;""",
        
        """CREATE TRIGGER trg_set_order_number_if_missing
           AFTER INSERT ON orders
           FOR EACH ROW
           WHEN (NEW.order_number IS NULL OR NEW.order_number = '')
           EXECUTE FUNCTION trg_set_order_number_if_missing_fn();"""
    ]
    
    # Execute trigger creations
    for stmt in triggers:
        try:
            execute(stmt)
        except Exception:
            pass
