"""GET /registrations/{email} - View a participant's registrations."""
import os

import boto3

from utils import response, is_valid_email  # noqa: E402

dynamodb = boto3.resource("dynamodb")
registrations_table = dynamodb.Table(os.environ["REGISTRATIONS_TABLE"])


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        email = (path_params.get("email") or "").strip().lower()

        if not is_valid_email(email):
            return response(400, {"error": "A valid email path parameter is required"})

        result = registrations_table.query(
            IndexName="emailIndex",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": email},
            ScanIndexForward=False,  # most recent first
        )

        return response(
            200, {"email": email, "registrations": result.get("Items", [])}
        )

    except Exception as e:
        print(f"Unhandled error in get_registrations handler: {e}")
        return response(500, {"error": "Internal server error"})
