from mcp.server.fastmcp import FastMCP
import sqlite3
from datetime import datetime, timedelta

mcp = FastMCP("PharmaInventory")

DB_NAME = "pharma.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# -----------------------------
# Create Database Table
# -----------------------------
conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT,
    category TEXT,
    quantity INTEGER,
    price REAL,
    expiry_date TEXT,
    supplier TEXT
)
""")

conn.commit()
conn.close()


# -----------------------------
# Add Medicine
# -----------------------------
@mcp.tool()
def add_medicine(
    medicine_name: str,
    category: str,
    quantity: int,
    price: float,
    expiry_date: str,
    supplier: str
):
    """Add medicine to inventory"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO medicines
        (
            medicine_name,
            category,
            quantity,
            price,
            expiry_date,
            supplier
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        medicine_name,
        category,
        quantity,
        price,
        expiry_date,
        supplier
    ))

    conn.commit()
    conn.close()

    return "Medicine added successfully"


# -----------------------------
# Show Inventory
# -----------------------------
@mcp.tool()
def show_inventory():
    """Show all medicines"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM medicines"
    )

    rows = cursor.fetchall()

    conn.close()

    return str(rows)


# -----------------------------
# Search Medicine
# -----------------------------
@mcp.tool()
def search_medicine(
    medicine_name: str
):
    """Search medicine by name"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM medicines
        WHERE medicine_name
        LIKE ?
    """, (f"%{medicine_name}%",))

    rows = cursor.fetchall()

    conn.close()

    return str(rows)


# -----------------------------
# Update Stock
# -----------------------------
@mcp.tool()
def update_stock(
    medicine_name: str,
    quantity: int
):
    """Update medicine stock"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE medicines
        SET quantity = ?
        WHERE medicine_name = ?
    """, (
        quantity,
        medicine_name
    ))

    conn.commit()
    conn.close()

    return "Stock updated"


# -----------------------------
# Reduce Stock
# -----------------------------
@mcp.tool()
def reduce_stock(
    medicine_name: str,
    amount: int
):
    """Reduce medicine stock"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE medicines
        SET quantity =
        quantity - ?
        WHERE medicine_name = ?
    """, (
        amount,
        medicine_name
    ))

    conn.commit()
    conn.close()

    return "Stock reduced"


# -----------------------------
# Low Stock Alert
# -----------------------------
@mcp.tool()
def low_stock():
    """Show low stock medicines"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM medicines
        WHERE quantity < 10
    """)

    rows = cursor.fetchall()

    conn.close()

    return str(rows)


# -----------------------------
# Expiry Alert
# -----------------------------
@mcp.tool()
def expiring_soon():
    """Medicines expiring in 30 days"""

    future_date = (
        datetime.now()
        + timedelta(days=30)
    ).strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM medicines
        WHERE expiry_date <= ?
    """, (future_date,))

    rows = cursor.fetchall()

    conn.close()

    return str(rows)


# -----------------------------
# Delete Medicine
# -----------------------------
@mcp.tool()
def delete_medicine(
    medicine_name: str
):
    """Delete medicine"""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM medicines
        WHERE medicine_name = ?
    """, (medicine_name,))

    conn.commit()
    conn.close()

    return "Medicine deleted"


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    mcp.run(transport="sse")
    print("database ready")