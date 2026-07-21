import json
import os
import sys
import importlib.util

_HANDLER_PATH = os.path.join(os.path.dirname(__file__), "..", "lambda", "get_registrations", "handler.py")
_SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda", "shared")


def _load_handler():
    if _SHARED_DIR not in sys.path:
        sys.path.insert(0, _SHARED_DIR)
    spec = importlib.util.spec_from_file_location("get_registrations_handler", _HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_registrations_by_email(dynamodb_tables):
    dynamodb_tables["registrations"].put_item(
        Item={
            "registrationId": "r1",
            "email": "jane@example.com",
            "eventId": "evt1",
            "status": "confirmed",
            "registeredAt": "2026-01-01T00:00:00+00:00",
        }
    )
    dynamodb_tables["registrations"].put_item(
        Item={
            "registrationId": "r2",
            "email": "other@example.com",
            "eventId": "evt1",
            "status": "confirmed",
            "registeredAt": "2026-01-02T00:00:00+00:00",
        }
    )
    handler = _load_handler()

    event = {"pathParameters": {"email": "jane@example.com"}}
    result = handler.handler(event, {})

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert len(body["registrations"]) == 1
    assert body["registrations"][0]["registrationId"] == "r1"


def test_get_registrations_invalid_email(dynamodb_tables):
    handler = _load_handler()
    event = {"pathParameters": {"email": "not-an-email"}}
    result = handler.handler(event, {})
    assert result["statusCode"] == 400


def test_get_registrations_none_found(dynamodb_tables):
    handler = _load_handler()
    event = {"pathParameters": {"email": "nobody@example.com"}}
    result = handler.handler(event, {})
    body = json.loads(result["body"])
    assert result["statusCode"] == 200
    assert body["registrations"] == []
