"""GET /events - List all events."""
import os

import boto3

from utils import response  # noqa: E402

dynamodb = boto3.resource("dynamodb")
events_table = dynamodb.Table(os.environ["EVENTS_TABLE"])


def handler(event, context):
    try:
        items = []
        scan_kwargs = {}
        while True:
            result = events_table.scan(**scan_kwargs)
            items.extend(result.get("Items", []))
            if "LastEvaluatedKey" not in result:
                break
            scan_kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]

        # Derive a friendly status if not already stored
        for item in items:
            slots = item.get("availableSlots", 0)
            if slots <= 0:
                item["status"] = "Full"
            elif slots <= 5:
                item["status"] = "Limited"
            else:
                item["status"] = "Available"

        items.sort(key=lambda x: x.get("eventDate", ""))

        return response(200, {"events": items, "count": len(items)})

    except Exception as e:
        print(f"Unhandled error in list_events handler: {e}")
        return response(500, {"error": "Internal server error"})
