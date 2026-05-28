from includes.db import get_db_connection

conn = get_db_connection()

migrations = [

    # USERS TABLE (block + soft delete)
    "ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN blocked_at DATETIME DEFAULT NULL",

    "ALTER TABLE users ADD COLUMN deleted_at DATETIME DEFAULT NULL",

    # ORDERS TABLE (soft delete)
    "ALTER TABLE orders ADD COLUMN deleted_at DATETIME DEFAULT NULL",
]

for sql in migrations:
    try:
        conn.execute(sql)
        print("OK:", sql)
    except Exception as e:
        # avoids crashing if column already exists
        print("SKIP:", sql, "->", e)

conn.commit()
conn.close()

print("Migration finished.")