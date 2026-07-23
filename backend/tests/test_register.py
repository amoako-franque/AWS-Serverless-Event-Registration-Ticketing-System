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
