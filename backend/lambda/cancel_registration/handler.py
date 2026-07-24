"""DELETE /registration/{id} - Cancel a registration (soft delete).

Uses a transactional write to atomically mark the registration cancelled
AND restore the event's availableSlots, so the two never drift out of
sync even if the Lambda were interrupted mid-operation, or if two
concurrent cancel requests raced against each other.

"Soft delete" means we never remove the registration item - we just flip
its status to "cancelled". This preserves an audit trail (who registered
and when, even after cancelling) and is also what allows the register
handler to detect "this person cancelled, let them re-register" rather
than "this person never registered, this is brand new".
"""
import os
from datetime import datetime, timezone

import boto3

from utils import response  # noqa: E402

dynamodb = boto3.resource("dynamodb")
dynamodb_client = boto3.client("dynamodb")
registrations_table = dynamodb.Table(os.environ["REGISTRATIONS_TABLE"])
EVENTS_TABLE_NAME = os.environ["EVENTS_TABLE"]
REGISTRATIONS_TABLE_NAME = os.environ["REGISTRATIONS_TABLE"]


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        registration_id = (path_params.get("id") or "").strip()

        if not registration_id:
            return response(400, {"error": "registration id path parameter is required"})

        # Plain read first, purely to distinguish "doesn't exist" (404)
        # from "exists but already cancelled" (409) with a clean error
        # message. The actual cancel-and-restore-capacity operation
        # below is still fully guarded by its own ConditionExpression,
        # so this read isn't load-bearing for correctness - just for a
        # nicer error message on the common case.
        reg = registrations_table.get_item(
            Key={"registrationId": registration_id}
        ).get("Item")

        if not reg:
            return response(404, {"error": "Registration not found"})

        if reg.get("status") == "cancelled":
            return response(409, {"error": "Registration is already cancelled"})

        now = datetime.now(timezone.utc).isoformat()

        # Atomically: (1) flip this registration to cancelled, and
        # (2) give the event's capacity slot back. If either half fails,
        # neither happens - e.g. if two cancel requests for the SAME
        # registration race each other, only one can win the
        # ConditionExpression below; the loser's transaction is
        # cancelled and the event's capacity is only restored once.
        try:
            dynamodb_client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": REGISTRATIONS_TABLE_NAME,
                            "Key": {"registrationId": {"S": registration_id}},
                            "UpdateExpression": (
                                "SET #s = :cancelled, cancelledAt = :now"
                            ),
                            # Only cancel if it's currently "confirmed" -
                            # this is what prevents a double-cancel from
                            # incrementing availableSlots twice.
                            "ConditionExpression": "#s = :confirmed",
                            "ExpressionAttributeNames": {"#s": "status"},
                            "ExpressionAttributeValues": {
                                ":cancelled": {"S": "cancelled"},
                                ":confirmed": {"S": "confirmed"},
                                ":now": {"S": now},
                            },
                        }
                    },
                    {
                        "Update": {
                            "TableName": EVENTS_TABLE_NAME,
                            "Key": {"eventId": {"S": reg["eventId"]}},
                            "UpdateExpression": (
                                "SET availableSlots = availableSlots + :one"
                            ),
                            "ExpressionAttributeValues": {":one": {"N": "1"}},
                        }
                    },
                ]
            )
        except dynamodb_client.exceptions.TransactionCanceledException:
            # In practice this means someone else cancelled the same
            # registration in the moment between our read above and this
            # write - a legitimate race, not a bug. Report it the same
            # way as the "already cancelled" case above.
            return response(409, {"error": "Registration is already cancelled"})

        return response(200, {"registrationId": registration_id, "status": "cancelled"})

    except Exception as e:
        print(f"Unhandled error in cancel_registration handler: {e}")
        return response(500, {"error": "Internal server error"})
    