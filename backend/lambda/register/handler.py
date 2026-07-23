"""POST /register - Register a participant for an event."""
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from utils import response, is_valid_email  # noqa: E402

dynamodb = boto3.resource("dynamodb")
events_table = dynamodb.Table(os.environ["EVENTS_TABLE"])
registrations_table = dynamodb.Table(os.environ["REGISTRATIONS_TABLE"])


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        event_id = (body.get("eventId") or "").strip()
        email = (body.get("email") or "").strip().lower()
        name = (body.get("name") or "").strip()

        if not event_id:
            return response(400, {"error": "eventId is required"})
        if not is_valid_email(email):
            return response(400, {"error": "A valid email is required"})
        if not name:
            return response(400, {"error": "name is required"})

        # Confirm event exists before touching capacity
        event_item = events_table.get_item(Key={"eventId": event_id}).get("Item")
        if not event_item:
            return response(404, {"error": "Event not found"})

        try:
            events_table.update_item(
                Key={"eventId": event_id},
                UpdateExpression="SET availableSlots = availableSlots - :one",
                ConditionExpression="availableSlots > :zero",
                ExpressionAttributeValues={":one": 1, ":zero": 0},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return response(409, {"error": "Event is full"})
            raise

        registration_id = str(uuid.uuid4())
        registrations_table.put_item(
            Item={
                "registrationId": registration_id,
                "eventId": event_id,
                "email": email,
                "name": name,
                "status": "confirmed",
                "registeredAt": datetime.now(timezone.utc).isoformat(),
            }
        )

        return response(
            201,
            {
                "registrationId": registration_id,
                "eventId": event_id,
                "status": "confirmed",
            },
        )

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON body"})
    except Exception as e:
        print(f"Unhandled error in register handler: {e}")
        return response(500, {"error": "Internal server error"})
