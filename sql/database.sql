-- ALChicken Database Schema
-- Complete schema including all features added during development
-- Drop tables if they exist (for fresh installation)
DROP TABLE IF EXISTS two_fa_codes;
DROP TABLE IF EXISTS password_resets;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS users;

-- ─── Users table ─────────────────────────────────────────────────────────────
CREATE TABLE users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    UNIQUE NOT NULL,
    password        TEXT    NOT NULL,
    name            TEXT    NOT NULL,
    phone           TEXT,
    address         TEXT,
    role            TEXT    DEFAULT 'customer',
    -- Two-step verification
    two_fa_enabled  INTEGER DEFAULT 0,
    two_fa_method   TEXT    DEFAULT NULL,
    -- Soft delete (30-day restore window)
    deleted_at      DATETIME DEFAULT NULL,
    restore_by      DATETIME DEFAULT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Products table ───────────────────────────────────────────────────────────
CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    price       REAL    NOT NULL,
    stock       INTEGER DEFAULT 0,
    image_url   TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Orders table ─────────────────────────────────────────────────────────────
CREATE TABLE orders (
    order_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL,
    order_date         DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount       REAL    NOT NULL,
    tax_amount         REAL    NOT NULL,
    delivery_option    TEXT    NOT NULL,
    delivery_address   TEXT,
    contact_number     TEXT    NOT NULL,
    order_status       TEXT    DEFAULT 'pending',
    processing_message TEXT,
    -- Admin note (only visible to admin)
    note               TEXT    DEFAULT NULL,
    -- Customer note (submitted by customer, visible to both)
    customer_note      TEXT    DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ─── Order Items table ────────────────────────────────────────────────────────
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL,
    item_price    REAL    NOT NULL,
    FOREIGN KEY (order_id)    REFERENCES orders(order_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);

-- ─── Payments table ───────────────────────────────────────────────────────────
CREATE TABLE payments (
    payment_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id           INTEGER NOT NULL,
    payment_method     TEXT    NOT NULL,
    payment_status     TEXT    DEFAULT 'pending',
    payment_date       DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_proof_file TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ─── Messages table (contact form submissions) ────────────────────────────────
CREATE TABLE messages (
    message_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    email        TEXT    NOT NULL,
    subject      TEXT,
    message      TEXT    NOT NULL,
    message_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read      INTEGER DEFAULT 0
);

-- ─── Password resets table ────────────────────────────────────────────────────
CREATE TABLE password_resets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    token      TEXT    NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used       INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ─── Two-factor authentication codes table ────────────────────────────────────
CREATE TABLE two_fa_codes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    code       TEXT    NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used       INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ─── Indexes for performance ──────────────────────────────────────────────────
CREATE INDEX idx_orders_user_id      ON orders(user_id);
CREATE INDEX idx_orders_status       ON orders(order_status);
CREATE INDEX idx_messages_is_read    ON messages(is_read);
CREATE INDEX idx_products_stock      ON products(stock);
CREATE INDEX idx_users_email         ON users(email);
CREATE INDEX idx_users_deleted       ON users(deleted_at);
CREATE INDEX idx_password_resets     ON password_resets(token);
CREATE INDEX idx_two_fa_codes        ON two_fa_codes(user_id);

-- ─── Default admin user ───────────────────────────────────────────────────────
-- Password hash is a placeholder - run init_db.py then set real password with:
-- python -c "from includes.auth import hash_password; from includes.db import get_db_connection; ..."
INSERT INTO users (email, password, name, role) VALUES
('adminalchicken@gmail.com', 'SET_PASSWORD_AFTER_INIT', 'Administrator', 'admin');

-- ─── Sample products ──────────────────────────────────────────────────────────
INSERT INTO products (name, description, price, stock, image_url) VALUES
('Whole Chicken',      'Fresh whole chicken, perfect for roasting. Approximately 3-4 lbs.',     1200.00, 20, 'whole-chicken.jpg'),
('Chicken Breast',     'Boneless, skinless chicken breasts. Pack of 4.',                         800.00,  30, 'chicken-breast.jpg'),
('Chicken Thighs',     'Juicy chicken thighs with skin. Pack of 6.',                             600.00,  25, 'chicken-thighs.jpg'),
('Chicken Wings',      'Perfect for grilling or frying. Pack of 12.',                            500.00,  40, 'chicken-wings.jpg'),
('Chicken Drumsticks', 'Fresh drumsticks. Pack of 8.',                                           550.00,  35, 'chicken-drumsticks.jpg'),
('Free Range Chicken', 'Organic free-range whole chicken. Approximately 4-5 lbs.',              1800.00,  10, 'free-range.jpg');