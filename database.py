# Lecture 7.6 - Wrap SQLite in a Database class
import sqlite3
from typing import Any

from schemas_fields import ProductCreate, ProductUpdate

SEED = [
    (1001, "Wireless Mouse", 18.99, 42),
    (1002, "Mechanical Keyboard", 64.99, 18),
    (1003, "USB-C Hub", 29.99, 35),
    (1004, "Laptop Stand", 39.99, 12),
    (1005, "Webcam", 54.99, 25),
    (1006, "Bluetooth Speaker", 44.99, 30),
    (1007, "External SSD", 89.99, 10),
]


class Database:
    def __init__(self, path: str = "products.db"):
        # check_same_thread=False: FastAPI's threads share this connection
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # Table names can NOT be "?" placeholders, so it is hard-coded
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS product (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                stock INTEGER
            )
        """)

    def seed(self):
        """Insert the starter products only when the table is empty."""
        self.cur.execute("SELECT COUNT(*) FROM product")
        if self.cur.fetchone()[0] == 0:
            self.cur.executemany("INSERT INTO product VALUES (?, ?, ?, ?)", SEED)
            self.conn.commit()

    def create(self, product: ProductCreate) -> int:
        # Next id = MAX(id) + 1  (empty table -> MAX is None -> start at 1001)
        self.cur.execute("SELECT MAX(id) FROM product")
        last_id = self.cur.fetchone()[0]
        new_id = (last_id or 1000) + 1

        self.cur.execute(
            """
            INSERT INTO product
            VALUES (:id, :name, :price, :stock)
            """,
            {"id": new_id, **product.model_dump()},
        )
        self.conn.commit()
        return new_id

    def get(self, id: int) -> dict[str, Any] | None:
        self.cur.execute("SELECT * FROM product WHERE id = ?", (id,))
        row = self.cur.fetchone()          # a tuple, or None

        # tuple -> dict (order = table definition)
        return {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3],
        } if row else None

    def update(self, id: int, product: ProductUpdate) -> dict[str, Any] | None:
        # COALESCE(a, b) = "a unless it is NULL, then b"
        # -> fields the client did not send (None) keep their old value
        self.cur.execute(
            """
            UPDATE product SET
                price = COALESCE(:price, price),
                stock = COALESCE(:stock, stock)
            WHERE id = :id
            """,
            {"id": id, **product.model_dump()},
        )
        self.conn.commit()
        return self.get(id)

    def delete(self, id: int) -> None:
        self.cur.execute("DELETE FROM product WHERE id = ?", (id,))
        self.conn.commit()

    def close(self):
        self.conn.close()