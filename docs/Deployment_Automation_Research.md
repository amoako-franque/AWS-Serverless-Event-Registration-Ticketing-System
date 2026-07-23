# Research: Deployment Automation Tools & Techniques

## Phase 3 — Automation & CI/CD

This document covers research into deployment automation tools and techniques considered for this project, and explains the reasoning behind the choices made.

---

## 1. Why deployment automation matters here

Before this project, the "deployment process" for the organization was manual: someone updated a spreadsheet or form by hand. Even after moving to AWS, deployments *could* still be manual — a developer running CLI commands from their laptop to push Lambda code and infrastructure changes. That approach doesn't scale for a team and reintroduces the same risk the project set out to remove: inconsistent, error-prone, undocumented changes.

Deployment automation solves this by making every deployment:
- **Repeatable** — the same steps run the same way every time
- **Reviewable** — changes go through pull requests before deploying
- **Auditable** — every deployment has a log of what changed and when
- **Fast to roll back** — previous versions are one redeploy away

---

## 2. CI/CD platforms considered

| Tool | Pros | Cons | Verdict |
|---|---|---|---|
| **GitHub Actions** | Native to GitHub (no extra account), free tier generous for small teams, huge marketplace of pre-built actions (AWS deploy, Terraform, Node setup), YAML config lives in the repo | Slightly less powerful than dedicated CD tools for complex multi-environment pipelines | **Chosen** — matches where the code already lives, zero extra infrastructure to manage |
| **AWS CodePipeline / CodeBuild** | Deep native AWS integration, IAM-based auth (no long-lived keys needed) | Adds AWS console complexity, less familiar to a student/early-career team, pricing outside free tier at higher usage | Considered, not chosen — GitHub Actions is simpler to learn and free for public/small repos |
| **CircleCI** | Fast builds, good caching | Another third-party account/service to manage, free tier more limited than GitHub Actions | Not chosen |
| **Jenkins** | Extremely flexible, self-hosted, industry-standard | Requires managing your own server (defeats the "serverless, low-maintenance" goal of this project) | Not chosen |
| **GitLab CI/CD** | Similar strengths to GitHub Actions | Repo isn't hosted on GitLab, would require mirroring | Not chosen |

**Decision: GitHub Actions**, since the codebase already lives on GitHub, it requires no separate server or account, and it has first-class support for both Node.js/Lambda testing and AWS deployment actions.

---

## 3. Infrastructure-as-Code (IaC) tools considered

Deployment automation isn't just about running scripts — it also needs a way to describe and version-control the AWS resources themselves.

| Tool | Pros | Cons |
|---|---|---|
| **Terraform** | Cloud-agnostic, huge community, state file gives clear drift detection, widely used in industry (strong resume value) | Requires managing a state file (locally or in S3 backend) |
| **AWS SAM (Serverless Application Model)** | Purpose-built for serverless apps, simpler syntax for Lambda + API Gateway, local testing with `sam local` | AWS-only, smaller community than Terraform |
| **AWS CDK** | Infrastructure defined in real code (TypeScript/Python/etc.), good for complex logic | Steeper learning curve, another build step (synth to CloudFormation) |
| **Raw CloudFormation** | No extra tooling needed, native AWS | Verbose YAML/JSON, harder to read and maintain |

**Decision:** Terraform (or AWS SAM, depending on team preference — see README) for its clarity, strong documentation, and transferability beyond AWS.

---

## 4. Deployment automation techniques evaluated

### 4.1 Branching strategy
- **Trunk-based (single `main` branch + short-lived feature branches)** — chosen for simplicity given team size; every merge to `main` triggers deployment.
- **Git Flow (develop/staging/main)** — considered for larger teams needing separate environments, but adds overhead not justified at this project's scale.

### 4.2 Testing before deploy
- Automated unit tests for Lambda handlers run on every push and pull request, before any deployment step executes.
- Pipeline fails fast — if tests fail, deployment does not proceed, preventing broken code from reaching AWS.

### 4.3 Validation of infrastructure changes
- `terraform plan` (or `sam validate`) runs in the pipeline to show exactly what will change before it's applied, and can be reviewed in a pull request.

### 4.4 Progressive/staged deployment
- Considered: separate `staging` and `production` AWS environments/accounts, promoting a build from one to the other only after verification.
- Not implemented in this phase due to free-tier/account constraints, but documented as a future improvement (see `ARCHITECTURE.md` roadmap).

### 4.5 Smoke testing after deploy
- A lightweight request to a known API endpoint runs immediately after deployment, confirming the API is live and responding correctly before the pipeline is marked successful.

### 4.6 Monitoring pipeline health
- GitHub Actions provides a built-in run history per workflow — every push shows pass/fail status, logs per step, and timing, giving the team visibility into build/deploy health without extra tooling.

---

## 5. Summary of decisions

| Area | Choice |
|---|---|
| CI/CD platform | GitHub Actions |
| IaC tool | Terraform (or AWS SAM) |
| Branching strategy | Trunk-based, short-lived feature branches |
| Testing | Automated unit tests gate every deployment |
| Validation | `terraform plan` / `sam validate` reviewed before apply |
| Post-deploy check | Smoke test against live API |
| Pipeline monitoring | Native GitHub Actions run logs and status checks |

These choices favor tools that are **free, well-documented, and low-maintenance** — appropriate for a small team building a portfolio-grade project within AWS's free tier, while still reflecting practices used in real production CI/CD pipelines.