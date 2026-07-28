"""Order Service API - Main application."""

import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, request
from marshmallow import Schema, fields, validate, ValidationError

import boto3

app = Flask(__name__)

# Configuration
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "orders")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


# --- Schemas for input validation ---

class OrderCreateSchema(Schema):
    customer_name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    customer_email = fields.Email(required=True)
    items = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))
    total_amount = fields.Float(required=True, validate=validate.Range(min=0.01))


class OrderUpdateSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(["pending", "processing", "shipped", "delivered", "cancelled"])
    )


order_create_schema = OrderCreateSchema()
order_update_schema = OrderUpdateSchema()


# --- DynamoDB client ---

def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(TABLE_NAME)


# --- Routes ---

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/orders", methods=["GET"])
def list_orders():
    """List all orders with pagination."""
    table = get_dynamodb_table()
    limit = request.args.get("limit", 20, type=int)
    limit = min(limit, 100)  # Cap at 100

    response = table.scan(Limit=limit)
    return jsonify({
        "orders": response.get("Items", []),
        "count": response.get("Count", 0)
    })


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Get a specific order by ID."""
    table = get_dynamodb_table()
    response = table.get_item(Key={"order_id": order_id})

    item = response.get("Item")
    if not item:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(item)


@app.route("/orders", methods=["POST"])
def create_order():
    """Create a new order."""
    try:
        data = order_create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "customer_name": data["customer_name"],
        "customer_email": data["customer_email"],
        "items": data["items"],
        "total_amount": str(data["total_amount"]),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    table = get_dynamodb_table()
    table.put_item(Item=order)

    return jsonify(order), 201


@app.route("/orders/<order_id>", methods=["PUT"])
def update_order(order_id):
    """Update an order's status."""
    try:
        data = order_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": "Validation failed", "details": err.messages}), 400

    table = get_dynamodb_table()

    # Verify order exists
    response = table.get_item(Key={"order_id": order_id})
    if not response.get("Item"):
        return jsonify({"error": "Order not found"}), 404

    table.update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET #s = :status, updated_at = :updated_at",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": data["status"],
            ":updated_at": datetime.utcnow().isoformat(),
        },
    )

    return jsonify({"message": "Order updated", "order_id": order_id, "status": data["status"]})


@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    """Delete an order."""
    table = get_dynamodb_table()

    # Verify order exists
    response = table.get_item(Key={"order_id": order_id})
    if not response.get("Item"):
        return jsonify({"error": "Order not found"}), 404

    table.delete_item(Key={"order_id": order_id})
    return jsonify({"message": "Order deleted", "order_id": order_id})


if __name__ == "__main__":
    import src.admin  # noqa: F401 - register admin routes
    app.run(host="0.0.0.0", port=5000, debug=True)
