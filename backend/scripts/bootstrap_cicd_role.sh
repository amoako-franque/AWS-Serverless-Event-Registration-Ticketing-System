#!/usr/bin/env bash
# Quick CLI bootstrap for GitHub Actions OIDC + deploy role.
# Simpler alternative to terraform-bootstrap/ for getting AWS_DEPLOY_ROLE_ARN fast.
#
# Usage:
#   ./scripts/bootstrap_cicd_role.sh YOUR_GITHUB_USERNAME event-ticketing-system
set -euo pipefail

GITHUB_ORG="${1:?Usage: $0 <github-org-or-username> <repo-name>}"
GITHUB_REPO="${2:?Usage: $0 <github-org-or-username> <repo-name>}"
ROLE_NAME="${GITHUB_REPO}-github-deploy"

echo "Checking for existing GitHub OIDC provider..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_ARN" >/dev/null 2>&1; then
  echo "OIDC provider already exists, reusing it."
else
  echo "Creating GitHub OIDC provider..."
  aws iam create-open-id-connect-provider \
    --url "https://token.actions.githubusercontent.com" \
    --client-id-list "sts.amazonaws.com" \
    --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1"
fi

echo "Creating trust policy for repo ${GITHUB_ORG}/${GITHUB_REPO} (main branch only)..."
cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "${OIDC_ARN}" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
      "StringLike": { "token.actions.githubusercontent.com:sub": "repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main" }
    }
  }]
}
EOF

echo "Creating IAM role ${ROLE_NAME}..."
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document file:///tmp/trust-policy.json

echo "Attaching AdministratorAccess (quick-start — swap for a scoped policy before production)..."
aws iam attach-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-arn "arn:aws:iam::aws:policy/AdministratorAccess"

ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

rm -f /tmp/trust-policy.json

echo ""
echo "Done. Add this as the AWS_DEPLOY_ROLE_ARN secret in your GitHub repo:"
echo ""
echo "  $ROLE_ARN"
echo ""