"""Admin API endpoints - privileged operations."""

import os
import functools

from flask import jsonify, request

from src.app import app


def require_admin_auth(f):
    """Authentication decorator for admin endpoints.

    Validates the API key from the Authorization header against
    the ADMIN_API_KEY environment variable.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[len("Bearer "):]
        expected_key = os.environ.get("ADMIN_API_KEY")
        if not expected_key:
            return jsonify({"error": "Admin API key not configured"}), 503
        if token != expected_key:
            return jsonify({"error": "Invalid API key"}), 403

        return f(*args, **kwargs)
    return decorated


# Allowed query fields to prevent information disclosure
ALLOWED_QUERY_FIELDS = {"customer_name", "customer_email", "status", "order_id"}


@app.route("/admin/users", methods=["GET"])
@require_admin_auth
def list_all_users():
    """List all users - admin only."""
    from src.app import orders_db
    customers = set()
    for order in orders_db.values():
        customers.add((order["customer_name"], order["customer_email"]))
    return jsonify([{"name": c[0], "email": c[1]} for c in customers])


@app.route("/admin/query", methods=["POST"])
@require_admin_auth
def run_query():
    """Run a query against orders with field validation."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    query_field = data.get("field")
    query_value = data.get("value")

    if not query_field or not query_value:
        return jsonify({"error": "Both 'field' and 'value' are required"}), 400

    if query_field not in ALLOWED_QUERY_FIELDS:
        return jsonify({
            "error": f"Invalid field. Allowed fields: {sorted(ALLOWED_QUERY_FIELDS)}"
        }), 400

    from src.app import orders_db
    results = []
    for order in orders_db.values():
        if str(order.get(query_field, "")) == str(query_value):
            results.append(order)
    return jsonify(results)


@app.route("/admin/export", methods=["GET"])
@require_admin_auth
def export_all_data():
    """Export entire database for backup."""
    from src.app import orders_db
    all_items = list(orders_db.values())
    return jsonify({
        "data": all_items,
        "count": len(all_items),
    })


@app.route("/admin/config", methods=["PUT"])
@require_admin_auth
def update_config():
    """Update application config at runtime (restricted keys only)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Only allow safe, application-specific config keys
    allowed_keys = {"LOG_LEVEL", "RATE_LIMIT", "FEATURE_FLAGS"}
    updated = []
    rejected = []

    for key, value in data.items():
        if key in allowed_keys:
            os.environ[key] = str(value)
            updated.append(key)
        else:
            rejected.append(key)

    response = {"message": "Config updated", "updated_keys": updated}
    if rejected:
        response["rejected_keys"] = rejected
        response["note"] = "Some keys were rejected (not in allowed list)"

    return jsonify(response)


@app.route("/admin/delete-all", methods=["DELETE"])
@require_admin_auth
def delete_all_orders():
    """Delete all orders from database (requires confirmation header)."""
    confirmation = request.headers.get("X-Confirm-Delete")
    if confirmation != "yes-delete-all":
        return jsonify({
            "error": "Confirmation required. Set header X-Confirm-Delete: yes-delete-all"
        }), 400

    from src.app import orders_db
    count = len(orders_db)
    orders_db.clear()
    return jsonify({"message": f"All {count} orders deleted"})
