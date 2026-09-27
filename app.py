from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "buybloom_secret_key"

DATABASE = "database.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # PRODUCTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # CART
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            UNIQUE(user_id, product_id)
        )
    """)

    # ORDERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Placed'
        )
    """)

    # ORDER ITEMS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Add products only if database is empty
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]

    if count == 0:
        products = [
            ("Wireless Headphones", "Electronics", 1499, 20),
            ("Smart Watch", "Electronics", 2499, 15),
            ("Bluetooth Speaker", "Electronics", 1799, 18),
            ("Wireless Mouse", "Electronics", 699, 30),
            ("Keyboard", "Electronics", 999, 25),
            ("Power Bank", "Electronics", 1299, 20),

            ("Cotton T-Shirt", "Fashion", 599, 30),
            ("Hoodie", "Fashion", 999, 20),
            ("Denim Jeans", "Fashion", 1499, 15),
            ("Backpack", "Fashion", 899, 18),
            ("Sneakers", "Fashion", 1999, 12),
            ("Cap", "Fashion", 399, 25),

            ("Notebook", "Stationery", 120, 50),
            ("Pen Set", "Stationery", 150, 40),
            ("Study Planner", "Stationery", 199, 30),
            ("Pencil Box", "Stationery", 249, 25),

            ("Water Bottle", "Home", 350, 25),
            ("Coffee Mug", "Home", 299, 30),
            ("Table Lamp", "Home", 799, 15),
            ("Cushion", "Home", 499, 20)
        ]

        cur.executemany("""
            INSERT INTO products
            (name, category, price, stock)
            VALUES (?, ?, ?, ?)
        """, products)

    conn.commit()
    conn.close()


# =========================================================
# PRODUCT IMAGES
# =========================================================

PRODUCT_IMAGES = {
    "Wireless Headphones":
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500",

    "Smart Watch":
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500",

    "Bluetooth Speaker":
        "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500",

    "Wireless Mouse":
        "https://images.unsplash.com/photo-1527814050087-3793815479db?w=500",

    "Keyboard":
        "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500",

    "Power Bank":
        "https://images.unsplash.com/photo-1609592424634-4e4c9a9c8f1e?w=500",

    "Cotton T-Shirt":
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",

    "Hoodie":
        "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500",

    "Denim Jeans":
        "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500",

    "Backpack":
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500",

    "Sneakers":
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500",

    "Cap":
        "https://images.unsplash.com/photo-1521369909029-2afed882baee?w=500",

    "Notebook":
        "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=500",

    "Pen Set":
        "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=500",

    "Study Planner":
        "https://images.unsplash.com/photo-1517842645767-c639042777db?w=500",

    "Pencil Box":
        "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=500",

    "Water Bottle":
        "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500",

    "Coffee Mug":
        "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=500",

    "Table Lamp":
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500",

    "Cushion":
        "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=500"
}


def add_images(products):
    result = []

    for product in products:
        item = dict(product)
        item["image"] = PRODUCT_IMAGES.get(
            item["name"],
            "https://via.placeholder.com/500x400?text=BuyBloom"
        )
        result.append(item)

    return result


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    conn = get_db()

    products = conn.execute("""
        SELECT * FROM products
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    products = add_images(products)

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("products"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# =========================================================
# PRODUCTS + SEARCH
# =========================================================

@app.route("/products")
def products():

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_db()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    # Search only matching products
    if search:
        query += """
            AND (
                name LIKE ?
                OR category LIKE ?
            )
        """

        params.append("%" + search + "%")
        params.append("%" + search + "%")

    # Category filter
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"

    products = conn.execute(
        query,
        params
    ).fetchall()

    categories = conn.execute("""
        SELECT DISTINCT category
        FROM products
        ORDER BY category
    """).fetchall()

    conn.close()

    products = add_images(products)

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category
    )


# =========================================================
# ADD TO CART
# =========================================================

@app.route(
    "/cart/add/<int:product_id>",
    methods=["POST"]
)
@login_required
def add_to_cart(product_id):

    user_id = session["user_id"]

    conn = get_db()

    product = conn.execute("""
        SELECT * FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if not product or product["stock"] <= 0:

        conn.close()

        return redirect(url_for("products"))

    existing = conn.execute("""
        SELECT * FROM cart
        WHERE user_id = ?
        AND product_id = ?
    """, (user_id, product_id)).fetchone()

    if existing:

        new_quantity = existing["quantity"] + 1

        if new_quantity <= product["stock"]:

            conn.execute("""
                UPDATE cart
                SET quantity = ?
                WHERE user_id = ?
                AND product_id = ?
            """, (
                new_quantity,
                user_id,
                product_id
            ))

    else:

        conn.execute("""
            INSERT INTO cart
            (user_id, product_id, quantity)
            VALUES (?, ?, 1)
        """, (
            user_id,
            product_id
        ))

    conn.commit()
    conn.close()

    return redirect(url_for("cart"))


# =========================================================
# CART
# =========================================================

@app.route("/cart")
@login_required
def cart():

    user_id = session["user_id"]

    conn = get_db()

    items = conn.execute("""
        SELECT
            cart.id,
            cart.quantity,
            products.name,
            products.price,
            products.stock,
            products.id AS product_id
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()

    conn.close()

    items = add_images(items)

    total = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


# =========================================================
# REMOVE CART ITEM
# =========================================================

@app.route(
    "/cart/remove/<int:cart_id>",
    methods=["POST"]
)
@login_required
def remove_cart(cart_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM cart
        WHERE id = ?
        AND user_id = ?
    """, (
        cart_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("cart"))


# =========================================================
# PLACE ORDER
# =========================================================

@app.route(
    "/order/place",
    methods=["POST"]
)
@login_required
def place_order():

    user_id = session["user_id"]

    conn = get_db()

    items = conn.execute("""
        SELECT
            cart.product_id,
            cart.quantity,
            products.price,
            products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()

    if not items:

        conn.close()

        return redirect(url_for("cart"))

    # Check stock
    for item in items:

        if item["quantity"] > item["stock"]:

            conn.close()

            return redirect(url_for("cart"))

    total = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    cur = conn.cursor()

    # Create order
    cur.execute("""
        INSERT INTO orders
        (user_id, total, status)
        VALUES (?, ?, 'Placed')
    """, (
        user_id,
        total
    ))

    order_id = cur.lastrowid

    # Add order items
    for item in items:

        cur.execute("""
            INSERT INTO order_items
            (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (
            order_id,
            item["product_id"],
            item["quantity"],
            item["price"]
        ))

        # Reduce stock
        cur.execute("""
            UPDATE products
            SET stock = stock - ?
            WHERE id = ?
        """, (
            item["quantity"],
            item["product_id"]
        ))

    # Clear cart
    cur.execute("""
        DELETE FROM cart
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("orders"))


# =========================================================
# ORDER HISTORY
# =========================================================

@app.route("/orders")
@login_required
def orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=orders
    )


# =========================================================
# CANCEL ORDER
# =========================================================

@app.route(
    "/order/cancel/<int:order_id>",
    methods=["POST"]
)
@login_required
def cancel_order(order_id):

    user_id = session["user_id"]

    conn = get_db()

    order = conn.execute("""
        SELECT *
        FROM orders
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        user_id
    )).fetchone()

    if not order:

        conn.close()

        return redirect(url_for("orders"))

    # Only placed orders can be cancelled
    if order["status"] != "Placed":

        conn.close()

        return redirect(url_for("orders"))

    # Get ordered products
    items = conn.execute("""
        SELECT *
        FROM order_items
        WHERE order_id = ?
    """, (order_id,)).fetchall()

    # Return stock
    for item in items:

        conn.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
        """, (
            item["quantity"],
            item["product_id"]
        ))

    # Change status
    conn.execute("""
        UPDATE orders
        SET status = 'Cancelled'
        WHERE id = ?
        AND user_id = ?
    """, (
        order_id,
        user_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("orders"))


# =========================================================
# API - ALL PRODUCTS
# =========================================================

@app.route("/api/products", methods=["GET"])
def api_products():

    conn = get_db()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY id
    """).fetchall()

    conn.close()

    result = []

    for product in products:

        result.append({
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "stock": product["stock"],
            "image": PRODUCT_IMAGES.get(
                product["name"],
                "https://via.placeholder.com/500x400?text=BuyBloom"
            )
        })

    return jsonify(result)


# =========================================================
# API - SINGLE PRODUCT
# =========================================================

@app.route(
    "/api/products/<int:product_id>",
    methods=["GET"]
)
def api_product(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    if not product:

        return jsonify({
            "error": "Product not found"
        }), 404

    return jsonify({
        "id": product["id"],
        "name": product["name"],
        "category": product["category"],
        "price": product["price"],
        "stock": product["stock"],
        "image": PRODUCT_IMAGES.get(
            product["name"],
            "https://via.placeholder.com/500x400?text=BuyBloom"
        )
    })


# =========================================================
# API - CATEGORIES
# =========================================================

@app.route(
    "/api/categories",
    methods=["GET"]
)
def api_categories():

    conn = get_db()

    categories = conn.execute("""
        SELECT DISTINCT category
        FROM products
        ORDER BY category
    """).fetchall()

    conn.close()

    return jsonify([
        category["category"]
        for category in categories
    ])


# =========================================================
# START APPLICATION
# =========================================================

init_db()


if __name__ == "__main__":
    app.run(debug=True)