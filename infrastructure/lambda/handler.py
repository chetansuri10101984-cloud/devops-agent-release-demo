"""Lambda handler for Order Service API.

This is a clean deployment version that uses DynamoDB for persistence
and API Gateway for HTTP routing. Used as the release testing target
in the workshop.
"""
import json
import uuid
import os
import boto3
from datetime import datetime
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["ORDERS_TABLE"])


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def response(status_code, body):
    """Standard API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def validate_order_input(data):
    """Validate order creation input."""
    errors = {}

    if not data.get("customer_name") or len(data["customer_name"].strip()) == 0:
        errors["customer_name"] = "Required, non-empty string"

    if not data.get("customer_email") or "@" not in data.get("customer_email", ""):
        errors["customer_email"] = "Valid email required"

    items = data.get("items", [])
    if not items or not isinstance(items, list) or len(items) == 0:
        errors["items"] = "At least one item required"
    else:
        for i, item in enumerate(items):
            if not item.get("product"):
                errors[f"items[{i}].product"] = "Required"
            if not isinstance(item.get("quantity"), int) or item["quantity"] < 1:
                errors[f"items[{i}].quantity"] = "Must be integer >= 1"
            if not isinstance(item.get("price"), (int, float)) or item["price"] <= 0:
                errors[f"items[{i}].price"] = "Must be number > 0"

    return errors


def handler(event, context):
    """Main Lambda handler - routes requests to appropriate function."""
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("path") or event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}

    # CORS preflight
    if http_method == "OPTIONS":
        return response(200, {})

    # Health check
    if path == "/api/health" and http_method == "GET":
        return health_check()

    # Stats
    if path == "/api/stats" and http_method == "GET":
        return get_stats()

    # Single order (path parameter routes - must check before collection routes)
    order_id = path_params.get("order_id") if path_params else None
    if order_id:
        if http_method == "GET":
            return get_order(order_id)
        elif http_method == "PUT":
            return update_order(order_id, event)
        elif http_method == "DELETE":
            return delete_order(order_id)

    # Orders collection
    if path == "/api/orders" and http_method == "GET":
        return list_orders(event)

    if path == "/api/orders" and http_method == "POST":
        return create_order(event)

    return response(404, {"error": "Not found"})


def health_check():
    """Health check endpoint."""
    return response(200, {
        "status": "healthy",
        "service": "order-service",
        "version": "1.2.0",
        "timestamp": datetime.utcnow().isoformat(),
    })


def get_stats():
    """Get order statistics."""
    result = table.scan()
    orders = result.get("Items", [])

    total_revenue = sum(float(o.get("total_amount", 0)) for o in orders)
    status_counts = {}
    for o in orders:
        status = o.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    return response(200, {
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "status_breakdown": status_counts,
    })


def list_orders(event):
    """List orders with optional status filter."""
    params = event.get("queryStringParameters") or {}
    status_filter = params.get("status")

    result = table.scan()
    orders = result.get("Items", [])

    if status_filter:
        orders = [o for o in orders if o.get("status") == status_filter]

    # Sort by created_at descending
    orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    orders = orders[:50]

    return response(200, {
        "orders": orders,
        "count": len(orders),
    })


def get_order(order_id):
    """Get a single order."""
    result = table.get_item(Key={"order_id": order_id})

    if "Item" not in result:
        return response(404, {"error": "Order not found"})

    return response(200, result["Item"])


def create_order(event):
    """Create a new order."""
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON body"})

    errors = validate_order_input(body)
    if errors:
        return response(400, {"error": "Validation failed", "details": errors})

    # Calculate total
    total_amount = sum(
        float(item["price"]) * item["quantity"] for item in body["items"]
    )

    order_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    order = {
        "order_id": order_id,
        "customer_name": body["customer_name"],
        "customer_email": body["customer_email"],
        "items": [
            {
                "product": item["product"],
                "quantity": item["quantity"],
                "price": Decimal(str(item["price"])),
            }
            for item in body["items"]
        ],
        "shipping_address": body.get("shipping_address", ""),
        "total_amount": Decimal(str(round(total_amount, 2))),
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    table.put_item(Item=order)

    return response(201, order)


def update_order(order_id, event):
    """Update an order's status."""
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON body"})

    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    new_status = body.get("status")

    if not new_status or new_status not in valid_statuses:
        return response(400, {
            "error": "Validation failed",
            "details": {"status": f"Must be one of: {', '.join(valid_statuses)}"},
        })

    # Check order exists
    result = table.get_item(Key={"order_id": order_id})
    if "Item" not in result:
        return response(404, {"error": "Order not found"})

    now = datetime.utcnow().isoformat()

    table.update_item(
        Key={"order_id": order_id},
        UpdateExpression="SET #s = :status, updated_at = :updated",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": new_status,
            ":updated": now,
        },
    )

    order = result["Item"]
    order["status"] = new_status
    order["updated_at"] = now

    return response(200, {"message": "Order updated", "order": order})


def delete_order(order_id):
    """Delete an order."""
    result = table.get_item(Key={"order_id": order_id})
    if "Item" not in result:
        return response(404, {"error": "Order not found"})

    table.delete_item(Key={"order_id": order_id})

    return response(200, {"message": "Order deleted", "order_id": order_id})
