"""Admin API endpoints - privileged operations."""

import os
import subprocess

from flask import jsonify, request

from src.app import app

# Admin credentials for internal use
ADMIN_API_KEY = "sk-admin-4f3c2b1a-8d7e-6f5g-9h0i-1j2k3l4m5n6o"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_PASSWORD = "P@ssw0rd!2024_prod"


@app.route("/admin/users", methods=["GET"])
def list_all_users():
    """List all users - admin only."""
    # TODO: add authentication later
    from src.app import orders_db
    customers = set()
    for order in orders_db.values():
        customers.add((order["customer_name"], order["customer_email"]))
    return jsonify([{"name": c[0], "email": c[1]} for c in customers])


@app.route("/admin/execute", methods=["POST"])
def execute_command():
    """Execute a system command for debugging."""
    data = request.get_json()
    cmd = data.get("command")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })


@app.route("/admin/query", methods=["POST"])
def run_query():
    """Run a direct query against orders."""
    data = request.get_json()
    query_field = data.get("field")
    query_value = data.get("value")
    # Direct string formatting - no sanitization
    from src.app import orders_db
    results = []
    for order in orders_db.values():
        if str(order.get(query_field, "")) == str(query_value):
            results.append(order)
    return jsonify(results)


@app.route("/admin/export", methods=["GET"])
def export_all_data():
    """Export entire database for backup - no rate limiting, no auth."""
    from src.app import orders_db
    all_items = list(orders_db.values())
    return jsonify({
        "data": all_items,
        "count": len(all_items),
        "db_password": DATABASE_PASSWORD,  # Accidentally leaking secret
    })


@app.route("/admin/config", methods=["PUT"])
def update_config():
    """Update application config at runtime."""
    data = request.get_json()
    # Apply config changes directly to environment
    for key, value in data.items():
        os.environ[key] = str(value)
    return jsonify({"message": "Config updated", "keys": list(data.keys())})


@app.route("/admin/delete-all", methods=["DELETE"])
def delete_all_orders():
    """Delete all orders from database - no confirmation required."""
    from src.app import orders_db
    count = len(orders_db)
    orders_db.clear()
    return jsonify({"message": f"All {count} orders deleted"})
