# Deployment Guide

## AWS Serverless Event Registration & Ticketing System

This document walks through deploying the system to AWS — both manually (for first-time setup) and automatically (via the CI/CD pipeline).

---

## 1. Prerequisites

Before deploying, make sure you have:

- An **AWS account** (free tier is sufficient)
- **AWS CLI** installed and configured with credentials (`aws configure`)
- **Node.js** installed (for Lambda functions and the frontend)
- **Terraform** (or **AWS SAM CLI**, depending on which IaC tool the `/infra` folder uses)
- **Git** installed locally
- Repo access on GitHub, with permission to push to `main` and configure repository secrets

---

## 2. Environment setup

Clone the repository:

```bash
git clone https://github.com/amoako-franque/AWS-Serverless-Event-Registration-Ticketing-System.git
cd AWS-Serverless-Event-Registration-Ticketing-System
 
```

Install backend dependencies:

```bash
npm install
```

---

## 3. Backend deployment (manual, first-time)

The backend (API Gateway, Lambda, DynamoDB, SNS, CloudWatch, Budgets) is defined as Infrastructure as Code in `/infra`.

```bash
cd infra
terraform init
terraform plan     # review what will be created
terraform apply    # provisions the AWS resources
```

`terraform apply` will output the deployed **API Gateway base URL** — save this, as the frontend needs it.

### What gets created

- API Gateway REST API and routes
- Lambda functions and their IAM execution roles
- DynamoDB tables (`Events`, `Registrations`) in on-demand billing mode
- SNS topics (registration confirmation + admin alerts)
- CloudWatch log groups and alarms
- An AWS Budget with threshold alerts

---

## 4. Frontend deployment (S3)

The frontend (React + Vite) is deployed as a static site to an S3 bucket.

### 4.1 Configure the API URL

In `frontend/.env` (or the relevant Vite env file), set:

```
VITE_API_BASE_URL=<your API Gateway URL from step 3>
```

### 4.2 Build the frontend

```bash
cd frontend
npm install
npm run build
```

This produces a `dist/` folder with the static site.

### 4.3 Create and configure the S3 bucket (first-time only)

```bash
aws s3 mb s3://<your-bucket-name>
aws s3 website s3://<your-bucket-name> --index-document index.html --error-document index.html
```

Set the bucket policy to allow public read access to objects (required for static website hosting), then confirm static website hosting is enabled in the bucket properties.

### 4.4 Upload the build

```bash
aws s3 sync dist/ s3://<your-bucket-name> --delete
```

The site will be available at the S3 static website endpoint:
`http://<your-bucket-name>.s3-website-<region>.amazonaws.com`

---

## 5. Automated deployment via CI/CD

Once the initial infrastructure exists, all future deployments happen automatically through **GitHub Actions** on every push to `main`.

### 5.1 Required GitHub repository secrets

Configure these under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM credentials for deployment |
| `AWS_SECRET_ACCESS_KEY` | IAM credentials for deployment |
| `AWS_REGION` | Target AWS region |
| `S3_BUCKET_NAME` | Target bucket for the frontend |
| `API_BASE_URL` | Used to inject the correct URL into the frontend build |

Use an IAM user/role scoped to only the permissions needed for deployment (Lambda, API Gateway, DynamoDB, S3, IAM role updates) — avoid using root credentials.

### 5.2 Pipeline steps

The workflow in `.github/workflows/deploy.yml` runs:

1. **Install & test** — installs backend and frontend dependencies, runs unit tests
2. **Validate infrastructure** — lints/validates the Terraform (or SAM) templates
3. **Deploy backend** — applies infrastructure changes (`terraform apply` or `sam deploy`)
4. **Build & deploy frontend** — builds the Vite app with the correct API URL and syncs it to S3
5. **Smoke test** — sends a test request to the deployed API to confirm it's responding

If any step fails, the pipeline stops and the previous deployment remains live.

---

## 6. Rollback

If a deployment introduces a problem:

- **Backend:** revert the problematic commit and let the pipeline redeploy the previous Terraform state, or run `terraform apply` manually against the last known-good configuration.
- **Frontend:** re-run `aws s3 sync` with a previous build output, or redeploy from the last known-good commit.

---

## 7. Cost safety checklist

Before and after deploying, confirm:

- [ ] DynamoDB tables are set to **on-demand** billing, not provisioned
- [ ] AWS Budgets is configured with an active threshold and a working SNS/email alert
- [ ] No unused Lambda versions, log groups, or S3 buckets are left behind from testing
- [ ] CloudWatch log retention is set (e.g. 14–30 days) rather than "never expire," to avoid storage buildup

---

## 8. Teardown (optional)

To remove all deployed AWS resources:

```bash
cd infra
terraform destroy
```

Then manually empty and delete the S3 bucket used for the frontend:

```bash
aws s3 rm s3://<your-bucket-name> --recursive
aws s3 rb s3://<your-bucket-name>
```