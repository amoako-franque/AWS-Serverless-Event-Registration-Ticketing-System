"""Shared helpers used across all Lambda handlers.

Every handler imports from this module (it gets flattened into the same
zip as handler.py by package_lambdas.sh), so keep it dependency-free
and framework-agnostic - it should never import boto3 or anything
AWS-specific.
"""
import json
import decimal


class DecimalEncoder(json.JSONEncoder):
    """DynamoDB returns numbers as Decimal objects, which json.dumps()
    can't serialize by default. This converts them to a plain int when
    the value is a whole number, or a float otherwise."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def response(status_code, body):
    """Build the API Gateway (HTTP API, payload format 2.0) response
    shape every handler returns. CORS headers are included on every
    response, including error responses, so the frontend can read the
    error body instead of the browser silently blocking it."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,DELETE",
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def is_valid_email(email):
    """Deliberately loose validation - just enough to reject obvious
    junk ("not-an-email") without rejecting valid-but-unusual real
    addresses. Full RFC 5322 validation is overkill for this use case
    and tends to reject legitimate addresses."""
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and len(domain.split(".")[-1]) >= 2


def slugify(text):
    """Turn 'AWS Workshop Accra 2026' into 'aws-workshop-accra-2026'.

    Used by create_event to derive a URL-safe, deterministic eventId
    from eventName when the caller doesn't supply one explicitly. Any
    run of non-alphanumeric characters collapses to a single dash, and
    leading/trailing dashes are stripped.
    """
    text = text.strip().lower()
    slug_chars = []
    prev_dash = False
    for ch in text:
        if ch.isalnum():
            slug_chars.append(ch)
            prev_dash = False
        elif not prev_dash:
            # Collapse any run of spaces/punctuation into one dash,
            # so "AWS  Workshop!!" doesn't become "aws----workshop--".
            slug_chars.append("-")
            prev_dash = True
    return "".join(slug_chars).strip("-")


def is_valid_url(url):
    """Minimal check - just confirms it's http(s), not a full URL
    parser. Good enough to catch "not-a-url" without being a
    validation bottleneck for legitimate S3/CDN URLs."""
    if not url:
        return False
    return url.startswith("https://") or url.startswith("http://")