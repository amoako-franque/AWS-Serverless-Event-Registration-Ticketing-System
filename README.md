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

| Service | Role |
|---|---|
| **API Gateway** | Exposes REST endpoints for event creation, registration, and lookup |
| **Lambda** | Stateless business logic — validates input, writes to DynamoDB, publishes to SNS |
| **DynamoDB** | Stores `Events` and `Registrations` tables, on-demand billing to fit free-tier usage |
| **SNS** *(optional)* | Sends attendee confirmation emails on successful registration |
| **CloudWatch** | Collects logs/metrics from API Gateway and Lambda; alarms on errors or throttling |
| **AWS Budgets** | Tracks spend and alerts before the free tier is exceeded |
| **GitHub Actions** | Runs tests and deploys infrastructure/code on every push to `main` |
| **IAM** | Least-privilege roles scoped per Lambda function and service boundary |


## Features
 
- REST API for creating events and registering attendees
- Automatic email confirmation on successful registration
- Centralized logging and alarms for API/Lambda errors
- Budget alerts before any charges are incurred
- One-command deployment via GitHub Actions
- Infrastructure defined as code (Terraform / AWS SAM — see `/infra`)

## Project structure 

```


```


## API endpoints
 
| Method | Path | Description |
|---|---|---|
| `POST` | `/events` | Create a new event |
| `GET` | `/events/{eventId}` | Get event details |
| `POST` | `/events/{eventId}/register` | Register an attendee |
| `GET` | `/events/{eventId}/registrations` | List registrations for an event |
 
## Getting started
 
### Prerequisites
 
- AWS account (free tier)
- AWS CLI configured locally
- Node.js (or your chosen Lambda runtime)
- Terraform or AWS SAM CLI