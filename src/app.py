"""Order Service API - Main application."""

import uuid
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from marshmallow import Schema, fields, validate, ValidationError

app = Flask(__name__, static_folder="../frontend", static_url_path="")

# In-memory store for demo (swap with DynamoDB in production)
orders_db = {}


# --- Schemas for input validation ---

class OrderItemSchema(Schema):
    product = fields.String(required=True, validate=validate.Length(min=1, max=200))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0.01))


class OrderCreateSchema(Schema):
    customer_name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    customer_email = fields.Email(required=True)
    items = fields.List(fields.Nested(OrderItemSchema), required=True, validate=validate.Length(min=1))
    shipping_address = fields.String(required=False, validate=validate.Length(max=500))


class OrderUpdateSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"])
    )


order_create_schema = OrderCreateSchema()
order_update_schema = OrderUpdateSchema()


# --- Frontend Routes ---

@app.route("/")
def serve_frontend():
    """Serve the frontend dashboard."""
    return send_from_directory(app.static_folder, "index.html")


# --- API Routes ---

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "order-service",
        "version": "1.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "orders_count": len(orders_db),
    })


@app.route("/api/orders", methods=["GET"])
def list_orders():
    """List all orders with optional filtering."""
    status_filter = request.args.get("status")
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 100)

    orders = list(orders_db.values())

    if status_filter:
        orders = [o for o in orders if o["status"] == status_filter]

    # Sort by created_at descending (newest first)
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    orders = orders[:limit]

    return jsonify({
        "orders": orders,
        "count": len(orders),
        "total": len(orders_db),
    })


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Get a specific order by ID."""
    order = orders_db.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)


@app.route("/api/orders", methods=["POST"])
def create_order():
    """Create a new order."""
    try:
        data = order_create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    # Calculate total from items
    total_amount = sum(item["price"] * item["quantity"] for item in data["items"])

    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "customer_name": data["customer_name"],
        "customer_email": data["customer_email"],
        "items": data["items"],
        "shipping_address": data.get("shipping_address", ""),
        "total_amount": round(total_amount, 2),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    orders_db[order_id] = order
    return jsonify(order), 201


@app.route("/api/orders/<order_id>", methods=["PUT"])
def update_order(order_id):
    """Update an order's status."""
    try:
        data = order_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    order = orders_db.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order["status"] = data["status"]
    order["updated_at"] = datetime.utcnow().isoformat()

    return jsonify({"message": "Order updated", "order": order})


@app.route("/api/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    """Delete an order."""
    if order_id not in orders_db:
        return jsonify({"error": "Order not found"}), 404

    del orders_db[order_id]
    return jsonify({"message": "Order deleted", "order_id": order_id})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get order statistics for the dashboard."""
    orders = list(orders_db.values())
    total_revenue = sum(float(o["total_amount"]) for o in orders)
    status_counts = {}
    for o in orders:
        status_counts[o["status"]] = status_counts.get(o["status"], 0) + 1

    return jsonify({
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "status_breakdown": status_counts,
        "recent_orders": sorted(orders, key=lambda x: x["created_at"], reverse=True)[:5],
    })


if __name__ == "__main__":
    # Seed with sample data for demo
    from src.seed import seed_sample_data
    seed_sample_data(orders_db)

    # Register admin routes
    import src.admin  # noqa: F401

    print("\n  Order Service running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
