"""POST /events - Create a new event.

Deduplication: eventId defaults to a slug of eventName (e.g. "AWS Workshop
Accra 2026" -> "aws-workshop-accra-2026"). A conditional PutItem rejects
the write if that eventId already exists, so the same event name can't be
created twice by accident. Callers can also pass an explicit eventId to
override the generated slug (useful if two events would otherwise slugify
to the same string, e.g. two different "Cloud Summit" events in different
years - pass distinct eventIds to disambiguate).
"""
import json
import os

import boto3
from botocore.exceptions import ClientError

from utils import response, is_valid_url, slugify  # noqa: E402

dynamodb = boto3.resource("dynamodb")
events_table = dynamodb.Table(os.environ["EVENTS_TABLE"])


def handler(event, context):
    try:
        # --- 1. Parse and validate input ---
        body = json.loads(event.get("body") or "{}")
        event_name = (body.get("eventName") or "").strip()
        event_date = (body.get("eventDate") or "").strip()
        location = (body.get("location") or "").strip()
        # imageUrl is intended to point at an S3-hosted (or any
        # publicly reachable) event image; storage/upload of the
        # actual image file is out of scope here - this endpoint just
        # accepts and stores the URL string.
        image_url = (body.get("imageUrl") or "").strip()
        explicit_event_id = (body.get("eventId") or "").strip()

        try:
            capacity = int(body.get("capacity", 0))
        except (TypeError, ValueError):
            return response(400, {"error": "capacity must be a whole number"})

        if not event_name:
            return response(400, {"error": "eventName is required"})
        if not event_date:
            return response(400, {"error": "eventDate is required"})
        if capacity <= 0:
            return response(400, {"error": "capacity must be greater than 0"})
        if image_url and not is_valid_url(image_url):
            return response(400, {"error": "imageUrl must be a valid http(s) URL"})

        # eventId is the DynamoDB partition key, so it must be unique.
        # Deriving it from the name by default means callers don't have
        # to invent IDs themselves, while still allowing an explicit
        # override for edge cases (see module docstring above).
        event_id = explicit_event_id or slugify(event_name)
        if not event_id:
            return response(400, {"error": "Could not derive a valid eventId from eventName"})

        # capacity and availableSlots start equal - availableSlots is
        # the ONLY field register/cancel ever mutate; capacity stays
        # fixed as a record of the event's original size.
        item = {
            "eventId": event_id,
            "eventName": event_name,
            "eventDate": event_date,
            "capacity": capacity,
            "availableSlots": capacity,
        }
        # location and imageUrl are optional - only store them if the
        # caller actually provided a value, rather than writing empty
        # strings into DynamoDB.
        if location:
            item["location"] = location
        if image_url:
            item["imageUrl"] = image_url

        try:
            # attribute_not_exists(eventId) is the actual duplicate
            # guard - DynamoDB rejects this write atomically if an item
            # with this key already exists, closing the same kind of
            # race condition a "check then insert" approach would leave
            # open (two simultaneous create-event calls for the same
            # name could otherwise both pass a pre-check and both write).
            events_table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(eventId)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return response(
                    409,
                    {"error": f"An event with id '{event_id}' already exists"},
                )
            raise

        return response(201, item)

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON body"})
    except Exception as e:
        print(f"Unhandled error in create_event handler: {e}")
        return response(500, {"error": "Internal server error"})