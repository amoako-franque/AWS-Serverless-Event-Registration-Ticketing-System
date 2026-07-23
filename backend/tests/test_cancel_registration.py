import json
import os
import sys
import importlib.util

_HANDLER_PATH = os.path.join(os.path.dirname(__file__), "..", "lambda", "cancel_registration", "handler.py")
_SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda", "shared")


def _load_handler():
    if _SHARED_DIR not in sys.path:
        sys.path.insert(0, _SHARED_DIR)
    spec = importlib.util.spec_from_file_location("cancel_registration_handler", _HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cancel_registration_success(dynamodb_tables):
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt1", "eventName": "Workshop", "availableSlots": 5}
    )
    dynamodb_tables["registrations"].put_item(
        Item={
            "registrationId": "r1",
            "eventId": "evt1",
            "email": "jane@example.com",
            "status": "confirmed",
            "registeredAt": "2026-01-01T00:00:00+00:00",
        }
    )
    handler = _load_handler()

    event = {"pathParameters": {"id": "r1"}}
    result = handler.handler(event, {})

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["status"] == "cancelled"

    # Slot should be given back
    updated_event = dynamodb_tables["events"].get_item(Key={"eventId": "evt1"})["Item"]
    assert updated_event["availableSlots"] == 6


def test_cancel_registration_not_found(dynamodb_tables):
    handler = _load_handler()
    event = {"pathParameters": {"id": "nonexistent"}}
    result = handler.handler(event, {})
    assert result["statusCode"] == 404


def test_cancel_already_cancelled(dynamodb_tables):
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt1", "eventName": "Workshop", "availableSlots": 5}
    )
    dynamodb_tables["registrations"].put_item(
        Item={
            "registrationId": "r2",
            "eventId": "evt1",
            "email": "jane@example.com",
            "status": "cancelled",
            "registeredAt": "2026-01-01T00:00:00+00:00",
        }
    )
    handler = _load_handler()
    event = {"pathParameters": {"id": "r2"}}
    result = handler.handler(event, {})
    assert result["statusCode"] == 409
