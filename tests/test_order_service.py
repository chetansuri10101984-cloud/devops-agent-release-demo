import json
import pytest
from unittest.mock import patch, MagicMock
from src.api.order_service import create_order, get_order

@pytest.fixture
def mock_context():
    context = MagicMock()
    context.aws_request_id = 'test-order-123'
    return context

class TestCreateOrder:
    def test_empty_items_returns_400(self, mock_context):
        event = {'body': json.dumps({'items': []})}
        result = create_order(event, mock_context)
        assert result['statusCode'] == 400
    
    def test_missing_items_returns_400(self, mock_context):
        event = {'body': json.dumps({})}
        result = create_order(event, mock_context)
        assert result['statusCode'] == 400

class TestGetOrder:
    def test_nonexistent_order_returns_404(self, mock_context):
        event = {'pathParameters': {'order_id': 'nonexistent'}}
        with patch('src.api.order_service.orders_table') as mock_table:
            mock_table.get_item.return_value = {}
            result = get_order(event, mock_context)
            assert result['statusCode'] == 404
