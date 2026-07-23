"""Shared helpers used across all Lambda handlers."""
import json
import decimal


class DecimalEncoder(json.JSONEncoder):
    """DynamoDB returns Decimal types; convert to int/float for JSON."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def response(status_code, body):
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
    if not email or "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and len(domain.split(".")[-1]) >= 2
