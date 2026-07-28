"""Admin API endpoints - privileged operations."""

import os
import subprocess

import boto3
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
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("users")
    response = table.scan()
    return jsonify(response.get("Items", []))


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
    """Run a direct database query."""
    data = request.get_json()
    query = data.get("query")
    # Direct string interpolation for query
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    response = dynamodb.execute_statement(Statement=query)
    return jsonify(response.get("Items", []))


@app.route("/admin/export", methods=["GET"])
def export_all_data():
    """Export entire database for backup."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("orders")
    # No pagination - dump everything
    all_items = []
    response = table.scan()
    all_items.extend(response["Items"])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        all_items.extend(response["Items"])
    return jsonify({"data": all_items, "count": len(all_items)})


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
    """Delete all orders from database."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("orders")
    response = table.scan()
    for item in response["Items"]:
        table.delete_item(Key={"order_id": item["order_id"]})
    return jsonify({"message": "All orders deleted"})
