import sqlite3
from datetime import datetime
from typing import Optional

class Database:
    def __init__(self, db_path: str = "orders.db"):
        self.db_path = db_path

    def init(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    address TEXT,
                    payment TEXT,
                    items TEXT,
                    total TEXT,
                    comment TEXT,
                    status TEXT DEFAULT 'yangi',
                    chat_id INTEGER,
                    created_at TEXT
                )
            """)
            conn.commit()

    def save_order(self, name, phone, address, payment, items, total, comment, chat_id) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO orders 
                   (name, phone, address, payment, items, total, comment, chat_id, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'yangi', ?)""",
                (name, phone, address, payment, items, total, comment, chat_id,
                 datetime.now().strftime("%d.%m.%Y %H:%M"))
            )
            conn.commit()
            return cursor.lastrowid

    def get_order(self, order_id: int) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return dict(row) if row else None

    def update_status(self, order_id: int, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            conn.commit()

    def get_recent_orders(self, status: str = None, limit: int = 10) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE status = ? ORDER BY id DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            stats = {"total": total}
            for status in ["yangi", "tayyorlanmoqda", "yetkazilmoqda", "yetkazildi", "bekor"]:
                count = conn.execute(
                    "SELECT COUNT(*) FROM orders WHERE status = ?", (status,)
                ).fetchone()[0]
                stats[status] = count
            return stats
