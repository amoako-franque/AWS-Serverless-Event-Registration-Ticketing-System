"""DELETE /registration/{id} - Cancel a registration (soft delete)."""
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from utils import response  # noqa: E402

dynamodb = boto3.resource("dynamodb")
registrations_table = dynamodb.Table(os.environ["REGISTRATIONS_TABLE"])
events_table = dynamodb.Table(os.environ["EVENTS_TABLE"])


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        registration_id = (path_params.get("id") or "").strip()

        if not registration_id:
            return response(400, {"error": "registration id path parameter is required"})

        reg = registrations_table.get_item(
            Key={"registrationId": registration_id}
        ).get("Item")

        if not reg:
            return response(404, {"error": "Registration not found"})

        if reg.get("status") == "cancelled":
            return response(409, {"error": "Registration is already cancelled"})

        try:
            registrations_table.update_item(
                Key={"registrationId": registration_id},
                UpdateExpression="SET #s = :cancelled, cancelledAt = :now",
                ConditionExpression="#s = :confirmed",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":cancelled": "cancelled",
                    ":confirmed": "confirmed",
                    ":now": datetime.now(timezone.utc).isoformat(),
                },
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return response(409, {"error": "Registration is already cancelled"})
            raise

        # Give the slot back
        events_table.update_item(
            Key={"eventId": reg["eventId"]},
            UpdateExpression="SET availableSlots = availableSlots + :one",
            ExpressionAttributeValues={":one": 1},
        )

        return response(200, {"registrationId": registration_id, "status": "cancelled"})

    except Exception as e:
        print(f"Unhandled error in cancel_registration handler: {e}")
        return response(500, {"error": "Internal server error"})
