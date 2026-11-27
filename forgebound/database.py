import hashlib
import hmac
import os
import sqlite3

from .config import DATA_DIR, DATABASE_PATH

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "ForgeAdmin123!"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password, stored_hash):
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 310_000
        )
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'customer')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_admin_only
                ON users(role) WHERE role = 'admin';

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                base_price INTEGER NOT NULL CHECK(base_price >= 0),
                description TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL REFERENCES users(id),
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                length_cm REAL NOT NULL,
                material TEXT NOT NULL,
                motif TEXT NOT NULL,
                handle_type TEXT NOT NULL DEFAULT 'Tidak ada',
                base_price INTEGER NOT NULL,
                extra_services TEXT NOT NULL DEFAULT '',
                total_price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Diterima',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        admin = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchone()
        if admin is None:
            conn.execute(
                """INSERT INTO users (full_name, username, email, password_hash, role)
                   VALUES (?, ?, ?, ?, 'admin')""",
                ("FORGEBOUND Administrator", ADMIN_USERNAME,
                 "admin@forgebound.local", hash_password(ADMIN_PASSWORD)),
            )

        conn.executemany(
            """INSERT OR IGNORE INTO products
               (code, name, category, base_price, description)
               VALUES (?, ?, ?, ?, ?)""",
            [
                ("GLK-001", "Golok", "Perkakas", 150000, "Golok tempa untuk kebutuhan umum."),
                ("CGL-001", "Cangkul", "Pertanian", 125000, "Cangkul untuk kebutuhan pertanian."),
                ("PGT-001", "Pagar Tempa", "Konstruksi", 500000, "Harga dasar simulasi per unit/panel."),
            ],
        )


def create_customer(full_name, username, email, password):
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO users (full_name, username, email, password_hash, role)
                   VALUES (?, ?, ?, ?, 'customer')""",
                (full_name.strip(), username.strip(), email.strip(), hash_password(password)),
            )
        return True, "Registrasi berhasil. Silakan login."
    except sqlite3.IntegrityError:
        return False, "Username atau email sudah digunakan."


def authenticate(username, password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),)
        ).fetchone()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def change_password(user_id, current_password, new_password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            return False, "Password saat ini tidak sesuai."
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
    return True, "Password berhasil diperbarui."
