import json
import boto3
import os
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
inventory_table = dynamodb.Table(os.environ['INVENTORY_TABLE'])

def create_order(event, context):
    """Create a new order with inventory check."""
    body = json.loads(event['body'])
    
    items = body.get('items', [])
    if not items:
        return response(400, {'error': 'Order must contain at least one item'})
    
    # Check inventory for all items
    unavailable = []
    for item in items:
        inventory = inventory_table.get_item(
            Key={'product_id': item['product_id']}
        ).get('Item')
        
        if not inventory or int(inventory['quantity']) < item['quantity']:
            unavailable.append(item['product_id'])
    
    if unavailable:
        return response(409, {
            'error': 'Insufficient inventory',
            'unavailable_items': unavailable
        })
    
    # Calculate total
    total = sum(Decimal(str(item['price'])) * item['quantity'] for item in items)
    
    # Create order
    order_id = context.aws_request_id
    order = {
        'order_id': order_id,
        'items': items,
        'total': str(total),
        'status': 'created',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    orders_table.put_item(Item=order)
    
    return response(201, {'order_id': order_id, 'total': str(total)})


def get_order(event, context):
    """Retrieve an order by ID."""
    order_id = event['pathParameters']['order_id']
    
    result = orders_table.get_item(Key={'order_id': order_id})
    
    if 'Item' not in result:
        return response(404, {'error': 'Order not found'})
    
    return response(200, result['Item'])


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body, default=str)
    }
