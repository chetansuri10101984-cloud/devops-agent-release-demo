"""Tests for Order Service API."""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"


def test_create_order_valid(client):
    with patch("src.app.get_dynamodb_table") as mock_table:
        mock_table.return_value = MagicMock()
        response = client.post(
            "/orders",
            data=json.dumps({
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "items": [{"product": "Widget", "quantity": 2}],
                "total_amount": 29.99,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["customer_name"] == "John Doe"
        assert data["status"] == "pending"


def test_create_order_invalid_email(client):
    response = client.post(
        "/orders",
        data=json.dumps({
            "customer_name": "John Doe",
            "customer_email": "not-an-email",
            "items": [{"product": "Widget", "quantity": 2}],
            "total_amount": 29.99,
        }),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_create_order_missing_fields(client):
    response = client.post(
        "/orders",
        data=json.dumps({"customer_name": "John Doe"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_update_order_invalid_status(client):
    with patch("src.app.get_dynamodb_table") as mock_table:
        mock_table.return_value = MagicMock()
        response = client.put(
            "/orders/some-id",
            data=json.dumps({"status": "invalid_status"}),
            content_type="application/json",
        )
        assert response.status_code == 400
