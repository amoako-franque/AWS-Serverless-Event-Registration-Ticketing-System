# Architecture Overview

## AWS Serverless Event Registration & Ticketing System

This document explains the architecture behind the system in detail — the services used, how data and requests flow between them, and why each design decision was made.

---

## 1. High-level summary

The system is a **serverless REST API** that replaces a manual Microsoft Forms + Excel registration workflow. It automatically scales with demand, sends attendees confirmation emails, monitors itself for errors, tracks its own AWS spend, and deploys through an automated CI/CD pipeline — all while staying inside the AWS free tier.

There are three main parts to the architecture:

1. **CI/CD pipeline** — how code gets from a developer's machine into AWS
2. **Core request flow** — how a client registration turns into a stored record and a confirmation email
3. **Observability & cost control** — how the team knows the system is healthy and within budget

---

## 2. Architecture diagram

![Event Ticketing Architecture](images/ticketing.drawio.png)

## 3. Component breakdown

### 3.1 CI/CD pipeline

| Step | What happens |
|---|---|
| Developer | Writes code locally (Lambda handlers, frontend, IaC) and pushes to GitHub |
| GitHub | Hosts the repository and triggers a workflow on push to `main` |
| GitHub Actions | Installs dependencies, runs tests, validates IaC, and deploys everything to AWS |

This removes manual, error-prone deployment steps — every change goes through the same automated checks before reaching production.

### 3.2 Core request flow

| Component | Role |
|---|---|
| **Client** | The React + Vite frontend (or any REST client) sends requests to create events or register attendees |
| **API Gateway** | Exposes REST endpoints (`/events`, `/events/{eventId}/register`, etc.) and routes requests to Lambda |
| **Lambda functions** | Stateless business logic — validates input, checks event capacity, writes to DynamoDB, and publishes to SNS on success |
| **DynamoDB** | NoSQL database with two tables: `Events` (event details, capacity) and `Registrations` (attendee records). On-demand billing mode is used so cost only accrues per request, avoiding idle capacity charges |
| **SNS (confirmation)** | Publishes a message after a successful registration, which triggers a confirmation email to the attendee |

This flow is entirely serverless — there are no servers to patch, scale, or pay for while idle. API Gateway and Lambda both scale automatically with registration volume, which directly solves the original bottleneck of a manual Forms + Excel process.

### 3.3 Observability & cost control

| Component | Role |
|---|---|
| **CloudWatch** | Collects logs and metrics from every API Gateway and Lambda invocation |
| **CloudWatch Alarm** | Watches for elevated error rates, throttling, or latency spikes |
| **SNS (admin alert)** | A separate SNS topic notifies the operations/admin team when an alarm fires — kept separate from the attendee confirmation topic so the two notification types don't mix |
| **AWS Budgets** | Tracks account-wide spend independently of the request flow and sends alerts at defined thresholds (e.g. 50%, 80%, 100%) to catch any usage approaching the free tier limit |

This gives the team real-time visibility into system health and cost — something the old manual process had no equivalent for.

### 3.4 Cross-cutting: IAM

**IAM roles** don't sit at one point in the diagram — they secure every arrow in it. Each Lambda function has its own least-privilege role (e.g. the registration Lambda can write to DynamoDB and publish to SNS, but nothing more), and API Gateway only has permission to invoke the specific Lambda functions it's wired to.

---

## 4. Why serverless?

| Old approach (Forms + Excel) | New approach (this architecture) |
|---|---|
| Manual data entry, no API | REST API with auto-scaling compute |
| No confirmation emails | Automatic email on registration via SNS |
| No error visibility | CloudWatch logs + alarms |
| No deployment process | GitHub Actions CI/CD on every push |
| No cost tracking | AWS Budgets with threshold alerts |
| Fixed, manual effort regardless of volume | Scales automatically with registration volume, at near-zero cost at low volume |

Serverless was chosen specifically because event registration traffic is **bursty** — high volume in the days before an event, near-zero the rest of the time. Paying only per-request (Lambda, API Gateway, DynamoDB on-demand) fits that pattern far better than provisioned servers or database capacity.

---

## 5. Possible future extensions

- **Cognito** — attendee/organizer authentication if login is needed
- **X-Ray** — distributed tracing across API Gateway → Lambda → DynamoDB for deeper debugging
- **Step Functions** — if registration becomes multi-step (e.g. payment → ticket generation → email)
- **S3 + Lambda** — QR-code ticket generation
- **CloudFront** — CDN in front of the S3-hosted frontend for lower latency and HTTPS by default