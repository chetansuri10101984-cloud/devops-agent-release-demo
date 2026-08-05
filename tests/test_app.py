"""Tests for Order Service API."""

import json
import pytest

from src.app import app, orders_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    orders_db.clear()
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_order():
    return {
        "customer_name": "Alice Johnson",
        "customer_email": "alice@example.com",
        "items": [
            {"product": "Wireless Keyboard", "quantity": 2, "price": 79.99},
            {"product": "USB-C Hub", "quantity": 1, "price": 45.00},
        ],
        "shipping_address": "123 Main St, Portland, OR 97201",
    }


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "order-service"

    def test_health_includes_order_count(self, client):
        response = client.get("/api/health")
        data = json.loads(response.data)
        assert "orders_count" in data


class TestCreateOrder:
    def test_create_valid_order(self, client, sample_order):
        response = client.post(
            "/api/orders",
            data=json.dumps(sample_order),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["customer_name"] == "Alice Johnson"
        assert data["status"] == "pending"
        assert data["total_amount"] == 204.98  # 79.99*2 + 45.00

    def test_create_order_missing_name(self, client):
        response = client.post(
            "/api/orders",
            data=json.dumps({
                "customer_email": "test@example.com",
                "items": [{"product": "Widget", "quantity": 1, "price": 10.0}],
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_order_invalid_email(self, client):
        response = client.post(
            "/api/orders",
            data=json.dumps({
                "customer_name": "Bob",
                "customer_email": "not-an-email",
                "items": [{"product": "Widget", "quantity": 1, "price": 10.0}],
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_order_empty_items(self, client):
        response = client.post(
            "/api/orders",
            data=json.dumps({
                "customer_name": "Bob",
                "customer_email": "bob@example.com",
                "items": [],
            }),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestListOrders:
    def test_list_empty(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["orders"] == []
        assert data["count"] == 0

    def test_list_with_orders(self, client, sample_order):
        client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")
        client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")

        response = client.get("/api/orders")
        data = json.loads(response.data)
        assert data["count"] == 2

    def test_filter_by_status(self, client, sample_order):
        client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")

        response = client.get("/api/orders?status=pending")
        data = json.loads(response.data)
        assert data["count"] == 1

        response = client.get("/api/orders?status=shipped")
        data = json.loads(response.data)
        assert data["count"] == 0


class TestUpdateOrder:
    def test_update_status(self, client, sample_order):
        create_resp = client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")
        order_id = json.loads(create_resp.data)["order_id"]

        response = client.put(
            f"/api/orders/{order_id}",
            data=json.dumps({"status": "shipped"}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_update_invalid_status(self, client, sample_order):
        create_resp = client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")
        order_id = json.loads(create_resp.data)["order_id"]

        response = client.put(
            f"/api/orders/{order_id}",
            data=json.dumps({"status": "invalid_status"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_nonexistent_order(self, client):
        response = client.put(
            "/api/orders/nonexistent-id",
            data=json.dumps({"status": "shipped"}),
            content_type="application/json",
        )
        assert response.status_code == 404


class TestDeleteOrder:
    def test_delete_existing(self, client, sample_order):
        create_resp = client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")
        order_id = json.loads(create_resp.data)["order_id"]

        response = client.delete(f"/api/orders/{order_id}")
        assert response.status_code == 200

        # Verify it's gone
        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 404

    def test_delete_nonexistent(self, client):
        response = client.delete("/api/orders/nonexistent-id")
        assert response.status_code == 404


class TestStats:
    def test_stats_empty(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total_orders"] == 0
        assert data["total_revenue"] == 0

    def test_stats_with_data(self, client, sample_order):
        client.post("/api/orders", data=json.dumps(sample_order), content_type="application/json")
        response = client.get("/api/stats")
        data = json.loads(response.data)
        assert data["total_orders"] == 1
        assert data["total_revenue"] == 204.98
