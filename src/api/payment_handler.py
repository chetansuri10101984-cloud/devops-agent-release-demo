import json
import boto3
import os

# Hardcoded credentials - SECURITY ISSUE
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'payments'))

def handler(event, context):
    """Process payment - no error handling."""
    body = json.loads(event['body'])
    
    # No input validation
    amount = body['amount']
    customer_id = body['customer_id']
    
    # Direct write without idempotency check
    table.put_item(Item={
        'customer_id': customer_id,
        'amount': amount,
        'status': 'processed'
    })
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Payment processed'})
    }
