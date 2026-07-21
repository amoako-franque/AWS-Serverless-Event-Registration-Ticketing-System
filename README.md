# AWS Serverless Event Registration & Ticketing System

Project Overview

The Event Registration & Ticketing System is a serverless application designed to replace a manual event registration process that relied on Microsoft Forms and Excel spreadsheets. The solution leverages AWS managed services to provide a scalable, secure, and cost-effective REST API for managing events and attendee registrations.

The application enables event organizers to create and manage events while allowing attendees to register online and receive automated confirmation emails. By adopting a serverless architecture, the system eliminates server management, automatically scales with demand, and minimizes operational costs.

## Problem

An event management organization was managing growing registration volumes through Microsoft Forms and Excel spreadsheets. This created:

No automated attendee confirmation emails
No real-time visibility into system health or errors
No structured, repeatable deployment process
No way to enforce spend limits or track cost against a free-tier budget

This project replaces that manual workflow with a serverless REST API that scales automatically, confirms registrations by email, tracks its own cost, and deploys through a CI/CD pipeline.

## Architecture overview

| Service              | Role                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------ |
| **API Gateway**      | Exposes REST endpoints for event creation, registration, and lookup                  |
| **Lambda**           | Stateless business logic — validates input, writes to DynamoDB, publishes to SNS     |
| **DynamoDB**         | Stores `Events` and `Registrations` tables, on-demand billing to fit free-tier usage |
| **SNS** _(optional)_ | Sends attendee confirmation emails on successful registration                        |
| **CloudWatch**       | Collects logs/metrics from API Gateway and Lambda; alarms on errors or throttling    |
| **AWS Budgets**      | Tracks spend and alerts before the free tier is exceeded                             |
| **GitHub Actions**   | Runs tests and deploys infrastructure/code on every push to `main`                   |
| **IAM**              | Least-privilege roles scoped per Lambda function and service boundary                |

## Features

- REST API for creating events and registering attendees
- Automatic email confirmation on successful registration
- Centralized logging and alarms for API/Lambda errors
- Budget alerts before any charges are incurred
- One-command deployment via GitHub Actions
- Infrastructure defined as code (Terraform / AWS SAM — see `/infra`)

## Project structure

```text
AWS-Serverless-Event-Registration-Ticketing-System/
├── backend/
│   └── BACKEND_DOC.md          # Backend documentation
├── frontend/
│   └── FRONTEND_DOC.md         # Frontend documentation
├── terraform/                  # Infrastructure as Code (Terraform or AWS SAM)
│   ├── backend/
│   │   └── .gitkeep
│   └── frontend/
│       └── .gitkeep
└── README.md                   # Project overview and setup guide
```

## API endpoints

| Method | Path                              | Description                     |
| ------ | --------------------------------- | ------------------------------- |
| `POST` | `/events`                         | Create a new event              |
| `GET`  | `/events/{eventId}`               | Get event details               |
| `POST` | `/events/{eventId}/register`      | Register an attendee            |
| `GET`  | `/events/{eventId}/registrations` | List registrations for an event |

## Getting started

## Git Workflow

This project follows a Git Flow branching strategy.

### Branches

- **main** – Production-ready code. Protected from direct pushes.
- **develop** – Integration branch for ongoing development.
- **feature/<feature-name>** – New features.
- **bugfix/<bug-name>** – Bug fixes.
- **hotfix/<issue-name>** – Critical production fixes.

### Development Process

1. Create a feature branch from `develop`:

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. Commit your changes:

   ```bash
   git add .
   git commit -m "Add feature"
   ```

3. Push the branch:

   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Open a Pull Request into `develop`.

5. After code review and approval, merge the Pull Request.

6. When a release is ready, merge `develop` into `main`.

### Branch Protection

The `main` branch is protected and requires:

- Pull requests before merging
- At least one approval
- No direct pushes
- No force pushes

### Prerequisites

- AWS account (free tier)
- AWS CLI configured locally
- Node.js (or your chosen Lambda runtime)
- Terraform or AWS SAM CLI

```

```
