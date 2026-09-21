import sqlite3
import bcrypt
import os
import logging

DB_NAME = "hardware_inventory.db"
LOG_FOLDER = "app_logging"

os.makedirs(LOG_FOLDER, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_FOLDER, "app.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # ======================================================
    # USERS TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL DEFAULT 'USER',
            failed_attempts INTEGER DEFAULT 0,
            locked_until REAL DEFAULT 0,
            is_locked INTEGER DEFAULT 0
        )
    """)

    # ======================================================
    # USERS TABLE MIGRATION
    # ======================================================

    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    migrations = {
        "email": "ALTER TABLE users ADD COLUMN email TEXT",
        "role": "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'USER'",
        "failed_attempts":
            "ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0",
        "locked_until":
            "ALTER TABLE users ADD COLUMN locked_until REAL DEFAULT 0",
        "is_locked":
            "ALTER TABLE users ADD COLUMN is_locked INTEGER DEFAULT 0"
    }

    for column, sql in migrations.items():

        if column not in columns:

            cursor.execute(sql)

            logging.info(
                f"Database migration: added column '{column}'"
            )

    # ======================================================
    # PASSWORD RESET REQUESTS
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            reviewed_at TEXT,
            reviewed_by TEXT
        )
    """)

    # ======================================================
    # HARDWARE TABLE
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hardware (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # ======================================================
    # HARDWARE AVAILABILITY MIGRATION
    # ======================================================

    cursor.execute("PRAGMA table_info(hardware)")

    hardware_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "available_quantity" not in hardware_columns:

        cursor.execute("""
            ALTER TABLE hardware
            ADD COLUMN available_quantity INTEGER
        """)

        cursor.execute("""
            UPDATE hardware
            SET available_quantity = quantity
            WHERE available_quantity IS NULL
        """)

        logging.info(
            "Database migration: added "
            "'available_quantity' to hardware."
        )

    cursor.execute("""
        UPDATE hardware
        SET available_quantity = quantity
        WHERE available_quantity IS NULL
    """)

    # ======================================================
    # BORROW REQUESTS TABLE
    #
    # One record = one borrowing slip
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrow_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            item_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            purpose TEXT NOT NULL,

            course TEXT NOT NULL,

            borrow_date TEXT NOT NULL,

            expected_return_date TEXT NOT NULL,

            notes TEXT,

            status TEXT NOT NULL DEFAULT 'PENDING',

            requested_at TEXT NOT NULL,

            reviewed_at TEXT,

            reviewed_by TEXT,

            return_requested_at TEXT,

            returned_at TEXT,

            return_confirmed_by TEXT,

            student_number TEXT
        )
    """)

    # ======================================================
    # BORROW REQUEST MIGRATION
    # ======================================================

    cursor.execute("PRAGMA table_info(borrow_requests)")

    borrow_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "student_number" not in borrow_columns:

        cursor.execute("""
            ALTER TABLE borrow_requests
            ADD COLUMN student_number TEXT
        """)

        logging.info(
            "Database migration: added "
            "'student_number' to borrow_requests."
        )

    # ======================================================
    # MULTIPLE COMPONENTS TABLE
    #
    # One borrow request can contain many components.
    # ======================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrow_request_items (
            borrow_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

            request_id INTEGER NOT NULL,

            item_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            FOREIGN KEY (request_id)
                REFERENCES borrow_requests(request_id),

            FOREIGN KEY (item_id)
                REFERENCES hardware(item_id)
        )
    """)

    # ======================================================
    # BORROW REQUEST INDEXES
    # ======================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_borrow_requests_username
        ON borrow_requests(username)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_borrow_requests_status
        ON borrow_requests(status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_borrow_request_items_request
        ON borrow_request_items(request_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_borrow_request_items_item
        ON borrow_request_items(item_id)
    """)

    # ======================================================
    # FIX OLD USERS
    # ======================================================

    cursor.execute("""
        UPDATE users
        SET role = 'USER'
        WHERE role IS NULL
        OR role = ''
    """)

    # ======================================================
    # DEFAULT ADMIN
    # ======================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE UPPER(role) = 'ADMIN'
    """)

    admin_count = cursor.fetchone()[0]

    if admin_count == 0:

        admin_password = "Admin@123"

        password_hash = bcrypt.hashpw(
            admin_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute("""
            INSERT OR IGNORE INTO users
            (
                username,
                password_hash,
                email,
                role,
                failed_attempts,
                locked_until,
                is_locked
            )
            VALUES (?, ?, ?, 'ADMIN', 0, 0, 0)
        """, (
            "admin",
            password_hash,
            "admin@campus.local"
        ))

        logging.info(
            "Default ADMIN account initialized."
        )

    conn.commit()
    conn.close()

    logging.info(
        "Database initialized successfully."
    )