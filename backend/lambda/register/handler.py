"""POST /register - Register a participant for an event.

Duplicate prevention: registrationId is a deterministic hash of
(eventId, email), so the same person registering for the same event twice
always maps to the same DynamoDB item. A transactional write atomically
decrements event capacity AND writes the registration, succeeding only if
the registration doesn't already exist as "confirmed" - this closes the
race condition an app-level check-then-write would leave open under
concurrent requests, and still allows re-registering after a cancellation.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from utils import response, is_valid_email  # noqa: E402

# boto3.resource is used for simple reads (the "does this event exist"
# check below); boto3.client is used for transact_write_items, which is
# only exposed on the low-level client, not the higher-level resource API.
dynamodb = boto3.resource("dynamodb")
dynamodb_client = boto3.client("dynamodb")
events_table = dynamodb.Table(os.environ["EVENTS_TABLE"])

# transact_write_items needs raw table names (not Table objects), so we
# keep these as plain strings pulled from the Lambda's environment vars
# (set by Terraform - see terraform/main.tf's lambda_register module).
EVENTS_TABLE_NAME = os.environ["EVENTS_TABLE"]
REGISTRATIONS_TABLE_NAME = os.environ["REGISTRATIONS_TABLE"]


def _registration_id(event_id, email):
    """Deterministic ID so the same (eventId, email) pair always maps to
    the same item. This is what makes the conditional write below able
    to detect and reject duplicate registrations - two requests for the
    same person+event collide on the SAME DynamoDB item, so DynamoDB's
    own conditional-write mechanism serializes them for us instead of
    us having to build locking logic ourselves.
    """
    raw = f"{event_id}:{email}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def handler(event, context):
    try:
        # --- 1. Parse and validate input ---
        body = json.loads(event.get("body") or "{}")
        event_id = (body.get("eventId") or "").strip()
        # Email is lowercased here so "Jane@Example.com" and
        # "jane@example.com" are treated as the same registrant - this
        # keeps the duplicate check and the deterministic ID consistent
        # regardless of how the caller capitalizes their email.
        email = (body.get("email") or "").strip().lower()
        name = (body.get("name") or "").strip()

        if not event_id:
            return response(400, {"error": "eventId is required"})
        if not is_valid_email(email):
            return response(400, {"error": "A valid email is required"})
        if not name:
            return response(400, {"error": "name is required"})

        # --- 2. Confirm the event exists before touching capacity ---
        # This is a plain read, not part of the transaction below - it's
        # just an early exit so we can return a clean 404 instead of
        # letting the transaction fail with a less informative error.
        # (The transaction's own condition still protects against a
        # race where the event gets deleted between this check and the
        # write - in that case the Update simply fails to match a key
        # and the transaction is cancelled.)
        event_item = events_table.get_item(Key={"eventId": event_id}).get("Item")
        if not event_item:
            return response(404, {"error": "Event not found"})

        registration_id = _registration_id(event_id, email)
        now = datetime.now(timezone.utc).isoformat()

        # --- 3. Atomically decrement capacity AND create the registration ---
        # Both operations succeed together or fail together (DynamoDB
        # transactions are all-or-nothing). This is the fix for two
        # separate bugs a naive two-step implementation would have:
        #   a) capacity could be decremented even if the registration
        #      write then failed for some other reason (e.g. duplicate)
        #   b) two concurrent requests for the same event could both
        #      pass a "slots > 0" check before either one writes,
        #      resulting in overselling
        try:
            dynamodb_client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": EVENTS_TABLE_NAME,
                            "Key": {"eventId": {"S": event_id}},
                            "UpdateExpression": "SET availableSlots = availableSlots - :one",
                            # Only allow the decrement if there's actually
                            # a slot left - this is what turns "Event is
                            # full" into an atomic, race-free check.
                            "ConditionExpression": "availableSlots > :zero",
                            "ExpressionAttributeValues": {
                                ":one": {"N": "1"},
                                ":zero": {"N": "0"},
                            },
                        }
                    },
                    {
                        "Put": {
                            "TableName": REGISTRATIONS_TABLE_NAME,
                            "Item": {
                                "registrationId": {"S": registration_id},
                                "eventId": {"S": event_id},
                                "email": {"S": email},
                                "name": {"S": name},
                                "status": {"S": "confirmed"},
                                "registeredAt": {"S": now},
                            },
                            # This condition is the actual duplicate-prevention
                            # logic: the write succeeds only if
                            #   (a) no item exists yet for this (eventId, email)
                            #       pair - i.e. a brand new registration, OR
                            #   (b) an item exists but its status is
                            #       "cancelled" - i.e. we're allowing the
                            #       person to re-register after cancelling.
                            # If an item exists with status "confirmed",
                            # neither branch matches, the condition fails,
                            # and the whole transaction is cancelled.
                            "ConditionExpression": (
                                "attribute_not_exists(registrationId) OR #s = :cancelled"
                            ),
                            "ExpressionAttributeNames": {"#s": "status"},
                            "ExpressionAttributeValues": {
                                ":cancelled": {"S": "cancelled"}
                            },
                        }
                    },
                ]
            )
        except dynamodb_client.exceptions.TransactionCanceledException as e:
            # DynamoDB reports which item's condition failed via
            # CancellationReasons, in the SAME ORDER as TransactItems
            # above - index 0 is the events-table Update, index 1 is the
            # registrations-table Put. We inspect both to return the
            # right error message to the caller.
            reasons = e.response.get("CancellationReasons", [])
            event_reason = reasons[0].get("Code") if len(reasons) > 0 else None
            reg_reason = reasons[1].get("Code") if len(reasons) > 1 else None

            if event_reason == "ConditionalCheckFailed":
                return response(409, {"error": "Event is full"})
            if reg_reason == "ConditionalCheckFailed":
                return response(
                    409, {"error": "You are already registered for this event"}
                )
            # Neither condition failed but the transaction was still
            # cancelled (e.g. a transient DynamoDB-side issue) - re-raise
            # so it's caught by the generic handler below and logged.
            raise

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
    except ClientError as e:
        print(f"DynamoDB error in register handler: {e}")
        return response(500, {"error": "Internal server error"})
    except Exception as e:
        print(f"Unhandled error in register handler: {e}")
        return response(500, {"error": "Internal server error"})