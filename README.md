# Order Service API

A simple REST API for managing orders, deployed on AWS with CloudFormation.

## Architecture

- **Runtime:** Python 3.12 / Flask
- **Infrastructure:** AWS CloudFormation (ECS Fargate, ALB, DynamoDB)
- **CI/CD:** GitHub Actions

## Local Development

```bash
pip install -r requirements.txt
python src/app.py
```

API runs on `http://localhost:5000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /orders | List all orders |
| GET | /orders/{id} | Get order by ID |
| POST | /orders | Create new order |
| PUT | /orders/{id} | Update order |
| DELETE | /orders/{id} | Delete order |

## Deployment

```bash
aws cloudformation deploy \
  --template-file infra/template.yaml \
  --stack-name order-service \
  --capabilities CAPABILITY_NAMED_IAM
```
