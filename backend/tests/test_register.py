import json
import os
import sys
import importlib.util

_HANDLER_PATH = os.path.join(os.path.dirname(__file__), "..", "lambda", "register", "handler.py")
_SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda", "shared")


def _load_handler():
    if _SHARED_DIR not in sys.path:
        sys.path.insert(0, _SHARED_DIR)
    spec = importlib.util.spec_from_file_location("register_handler", _HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_register_success(dynamodb_tables):
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt1", "eventName": "AWS Workshop", "availableSlots": 10}
    )
    handler = _load_handler()

    event = {
        "body": json.dumps(
            {"eventId": "evt1", "email": "test@example.com", "name": "Jane Doe"}
        )
    }
    result = handler.handler(event, {})

    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert body["status"] == "confirmed"
    assert "registrationId" in body


def test_register_missing_email(dynamodb_tables):
    handler = _load_handler()
    event = {"body": json.dumps({"eventId": "evt1", "name": "Jane Doe"})}
    result = handler.handler(event, {})
    assert result["statusCode"] == 400


def test_register_invalid_email(dynamodb_tables):
    handler = _load_handler()
    event = {
        "body": json.dumps(
            {"eventId": "evt1", "email": "not-an-email", "name": "Jane Doe"}
        )
    }
    result = handler.handler(event, {})
    assert result["statusCode"] == 400


def test_register_event_not_found(dynamodb_tables):
    handler = _load_handler()
    event = {
        "body": json.dumps(
            {"eventId": "nonexistent", "email": "test@example.com", "name": "Jane"}
        )
    }
    result = handler.handler(event, {})
    assert result["statusCode"] == 404


def test_register_event_full(dynamodb_tables):
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt2", "eventName": "Full Event", "availableSlots": 0}
    )
    handler = _load_handler()
    event = {
        "body": json.dumps(
            {"eventId": "evt2", "email": "test@example.com", "name": "Jane"}
        )
    }
    result = handler.handler(event, {})
    assert result["statusCode"] == 409

def test_register_duplicate_rejected(dynamodb_tables):
    """Registering the same email for the same event twice must fail on
    the second attempt, and must NOT double-decrement availableSlots."""
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt3", "eventName": "Dup Test", "availableSlots": 10}
    )
    handler = _load_handler()
    body = json.dumps(
        {"eventId": "evt3", "email": "dup@example.com", "name": "Dup Person"}
    )

    first = handler.handler({"body": body}, {})
    assert first["statusCode"] == 201
    first_id = json.loads(first["body"])["registrationId"]

    second = handler.handler({"body": body}, {})
    assert second["statusCode"] == 409
    assert "already registered" in json.loads(second["body"])["error"].lower()

    # Same deterministic ID both times, and slots decremented only once
    updated_event = dynamodb_tables["events"].get_item(Key={"eventId": "evt3"})["Item"]
    assert updated_event["availableSlots"] == 9

    reg = dynamodb_tables["registrations"].get_item(
        Key={"registrationId": first_id}
    )["Item"]
    assert reg["status"] == "confirmed"


def test_register_different_events_same_email_allowed(dynamodb_tables):
    """The duplicate check is scoped per-event - the same email can
    register for two DIFFERENT events without conflict."""
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt-a", "eventName": "Event A", "availableSlots": 5}
    )
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt-b", "eventName": "Event B", "availableSlots": 5}
    )
    handler = _load_handler()

    result_a = handler.handler(
        {"body": json.dumps({"eventId": "evt-a", "email": "multi@example.com", "name": "Multi"})},
        {},
    )
    result_b = handler.handler(
        {"body": json.dumps({"eventId": "evt-b", "email": "multi@example.com", "name": "Multi"})},
        {},
    )
    assert result_a["statusCode"] == 201
    assert result_b["statusCode"] == 201


def test_register_after_cancel_allowed(dynamodb_tables):
    """A cancelled registration should free the person to register again
    for the same event."""
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt4", "eventName": "Recycle Test", "availableSlots": 5}
    )
    handler = _load_handler()
    body = json.dumps(
        {"eventId": "evt4", "email": "recycle@example.com", "name": "Recycler"}
    )

    first = handler.handler({"body": body}, {})
    assert first["statusCode"] == 201
    reg_id = json.loads(first["body"])["registrationId"]

    # Simulate cancellation directly on the table (cancel handler tested separately)
    dynamodb_tables["registrations"].update_item(
        Key={"registrationId": reg_id},
        UpdateExpression="SET #s = :cancelled",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":cancelled": "cancelled"},
    )
    dynamodb_tables["events"].update_item(
        Key={"eventId": "evt4"},
        UpdateExpression="SET availableSlots = availableSlots + :one",
        ExpressionAttributeValues={":one": 1},
    )

    second = handler.handler({"body": body}, {})
    assert second["statusCode"] == 201
    # Deterministic ID means it's the SAME item, now flipped back to confirmed
    assert json.loads(second["body"])["registrationId"] == reg_id