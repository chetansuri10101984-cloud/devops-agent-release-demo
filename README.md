# Order Service - Release Validation Demo

A full-stack order management service used to demonstrate **automated release validation** — an AI agent that reviews code, infrastructure, and security before deployment.

## Quick Start

```bash
cd /Users/damkumar/workspace/devops-agent-release-demo
pip install -r requirements.txt
python -m src.app
```

Open **http://localhost:5000** in your browser.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (Vanilla JS Dashboard)            │
│  • Order management UI                      │
│  • Real-time stats                          │
│  • Create / Update / Delete orders          │
├─────────────────────────────────────────────┤
│  Backend (Flask REST API)                   │
│  • /api/orders - CRUD operations            │
│  • /api/stats - Dashboard statistics        │
│  • /api/health - Health check               │
│  • /admin/* - Admin endpoints (ISSUES HERE) │
├─────────────────────────────────────────────┤
│  Infrastructure (CloudFormation)            │
│  • ECS Fargate + ALB                        │
│  • DynamoDB                                 │
│  • S3 (ISSUES HERE)                         │
│  • IAM Roles (ISSUES HERE)                  │
└─────────────────────────────────────────────┘
```

## Demo Flow: Automated Release Validation

### 1. Show the Working Application
- Open http://localhost:5000
- Create some orders, update statuses, show the dashboard
- Point out this is a standard microservice ready for production

### 2. Ask the Agent to Validate for Release
Prompt: *"Review this application for production readiness. Check code quality, security, and infrastructure."*

### 3. Issues the Agent Should Find

**Code Security (src/admin.py):**
| # | Issue | Severity |
|---|-------|----------|
| 1 | Hardcoded AWS credentials and API keys | CRITICAL |
| 2 | Command injection via subprocess.run(shell=True) | CRITICAL |
| 3 | No authentication on admin endpoints | HIGH |
| 4 | Database password leaked in /admin/export response | HIGH |
| 5 | Unrestricted environment variable manipulation | MEDIUM |
| 6 | Bulk delete without confirmation/audit | MEDIUM |

**Infrastructure (infra/template.yaml):**
| # | Issue | Severity |
|---|-------|----------|
| 1 | IAM `Action: "*"` on `Resource: "*"` | CRITICAL |
| 2 | AdminRole assumable by `Principal: AWS: "*"` | CRITICAL |
| 3 | Security groups open all ports (0-65535) to 0.0.0.0/0 | HIGH |
| 4 | S3 bucket publicly accessible, no encryption | HIGH |
| 5 | No DeletionPolicy on DynamoDB table | MEDIUM |
| 6 | ECS SecurityGroup allows all inbound traffic | HIGH |

### 4. Agent Generates Fixes
The agent should propose:
- Move secrets to AWS Secrets Manager / environment variables
- Add authentication middleware to admin routes
- Scope IAM permissions to least privilege
- Restrict security groups to necessary ports only
- Enable S3 encryption + block public access
- Add DeletionPolicy: Retain to stateful resources

### 5. Agent Validates the Fix
- Re-run security scan on patched code
- Validate CloudFormation template
- Run tests to confirm nothing broke
- Generate deployment-ready PR

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/orders | List orders (filter: ?status=pending) |
| GET | /api/orders/{id} | Get order |
| POST | /api/orders | Create order |
| PUT | /api/orders/{id} | Update status |
| DELETE | /api/orders/{id} | Delete order |
| GET | /api/stats | Dashboard statistics |

## Project Structure

```
devops-agent-release-demo/
├── frontend/
│   └── index.html          # Dashboard UI
├── src/
│   ├── app.py              # Main API (clean)
│   ├── seed.py             # Sample data generator
│   └── admin.py            # Admin routes (intentional issues)
├── infra/
│   └── template.yaml       # CloudFormation (intentional issues)
├── tests/
│   └── test_app.py         # Unit tests
├── .github/workflows/
│   └── ci.yml              # CI/CD pipeline
├── requirements.txt
└── README.md
```
