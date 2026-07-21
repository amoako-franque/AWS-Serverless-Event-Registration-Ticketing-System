# Event Registration & Ticketing System — Backend

Serverless REST API backend for event registration, built on AWS Free Tier services, deployed via Terraform + GitHub Actions. — see [backend/API.md](./backend/API.md) for the contract they build against.

## Repository Structure

```
.
├── backend/
│   ├── lambda/              # one folder per function + shared/utils.py
│   ├── tests/                # pytest + moto (mocked AWS) unit tests
│   ├── scripts/
│   │   ├── package_lambdas.sh  # bundles each function into backend/build/*.zip
│   │   └── seed_events.py      # seeds demo events for the frontend team
│   ├── API.md                 # API contract for the frontend team
│   └── requirements*.txt
├── frontend/                # owned by the frontend team
├── terraform/
│   ├── main.tf               # root module wiring everything together
│   ├── variables.tf
│   ├── outputs.tf
│   ├── backend.tf            # provider + remote state config
│   └── modules/               # dynamodb, lambda, api-gateway, monitoring, budgets
├── .github/workflows/         # test.yml (CI) and deploy.yml (CD, auto-apply)
└── README.md
```

## Architecture

```
GitHub Repo → GitHub Actions (CI/CD) → Terraform → AWS
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
              API Gateway          4x Lambda (Python)      DynamoDB
              (HTTP API)          register / list_events /  (Events +
                                  get_registrations /       Registrations
                                  cancel_registration        tables)
                    │
              CloudWatch Alarms + SNS
              AWS Budgets (cost tracking)
```

**Design choices:**
- **API Gateway v2 (HTTP API)** instead of REST API — cheaper, simpler CORS, sufficient for Lambda-proxy integrations.
- **One Lambda per endpoint** — each function gets its own least-privilege IAM role scoped to only the DynamoDB actions it needs, and its own CloudWatch error-rate alarm.
- **DynamoDB with `PAY_PER_REQUEST` billing** — no capacity planning needed, stays within Free Tier for low/unpredictable traffic.
- **Soft-delete cancellations** — cancelling a registration sets `status: cancelled` rather than deleting the item, preserving an audit trail and freeing the event slot back up.
- **No frontend hosting in this Terraform** — the frontend team hosts their own app and consumes this API over HTTPS. CORS is controlled by the `frontend_origin` Terraform variable.

## API Endpoints

See [backend/API.md](./backend/API.md) for full request/response contracts.

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Register for an event |
| `GET` | `/events` | List all events with computed availability status |
| `GET` | `/registrations/{email}` | View a participant's registrations |
| `DELETE` | `/registration/{id}` | Cancel a registration |

## Getting Started

### Prerequisites
- AWS account with Free Tier available
- Terraform >= 1.6
- Python 3.12
- An AWS OIDC identity provider configured for GitHub Actions (for CI/CD deploys)

### 1. Bootstrap remote state (one-time, manual)
Create an S3 bucket and DynamoDB table for Terraform state locking, then uncomment the `backend "s3"` block in `terraform/backend.tf`.

### 2. Local development
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt --break-system-packages
pytest tests/ -v
flake8 lambda/
```

### 3. Package and deploy manually
```bash
./backend/scripts/package_lambdas.sh
cd terraform
terraform init
terraform plan -var="alert_email=you@example.com" -var="frontend_origin=*"
terraform apply -var="alert_email=you@example.com" -var="frontend_origin=*"
```

Once your teammate has a real frontend URL, redeploy with
`-var="frontend_origin=https://their-actual-domain.com"` to lock CORS down from `*`.

### 4. Seed demo data
```bash
python backend/scripts/seed_events.py --table $(terraform -chdir=terraform output -raw events_table_name)
```

### 5. Hand off to the frontend team
After `terraform apply`:
```bash
terraform -chdir=terraform output -raw api_url
```
Send them this URL + [backend/API.md](./backend/API.md).

### 6. Set up CI/CD
In your GitHub repo settings, add these secrets:
- `AWS_DEPLOY_ROLE_ARN` — IAM role ARN for GitHub OIDC to assume
- `ALERT_EMAIL` — email for CloudWatch alarm / budget notifications

Every push to `main` runs tests, then auto-deploys via Terraform, and prints the API URL at the end of the run.

## Monitoring

- **Per-function error rate alarms** — fires if any Lambda's error rate exceeds 5% over a 5-minute window.
- **Per-function duration alarms** — fires if p99 duration exceeds 5 seconds.
- **API Gateway 5XX alarm** — fires on elevated server errors.
- **SNS topic** — all alarms notify a single topic with an email subscription (output as `sns_alert_topic_arn` if you want to add more subscribers, e.g. Slack via a Lambda subscriber).
- **AWS Budgets** — monthly cost alert at 80% actual spend and 100% forecasted spend.

## Security

- Each Lambda has its own IAM role with only the specific DynamoDB actions it needs (principle of least privilege) — no wildcard permissions.
- Input validation happens in each handler (required fields, email format, capacity checks via conditional writes to prevent overselling under concurrent requests).
- Deployment uses GitHub OIDC federated roles — no long-lived AWS access keys stored in GitHub Secrets.
- CORS is restricted to `frontend_origin` in production — don't leave it as `*` once you have a real frontend URL.

## Cost

Everything here fits comfortably within AWS Free Tier for low-volume usage: DynamoDB on-demand billing, Lambda's 1M free monthly requests, and API Gateway's free tier. An AWS Budgets alert is configured as a safety net.
