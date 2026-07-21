import json
import os
import sys
import importlib.util

_HANDLER_PATH = os.path.join(os.path.dirname(__file__), "..", "lambda", "list_events", "handler.py")
_SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda", "shared")


def _load_handler():
    if _SHARED_DIR not in sys.path:
        sys.path.insert(0, _SHARED_DIR)
    spec = importlib.util.spec_from_file_location("list_events_handler", _HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_list_events_returns_all(dynamodb_tables):
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt1", "eventName": "AWS Workshop", "eventDate": "2026-05-15", "availableSlots": 10}
    )
    dynamodb_tables["events"].put_item(
        Item={"eventId": "evt2", "eventName": "Cloud Summit", "eventDate": "2026-06-28", "availableSlots": 3}
    )
    handler = _load_handler()

    result = handler.handler({}, {})
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["count"] == 2


def test_list_events_status_labels(dynamodb_tables):
    dynamodb_tables["events"].put_item(
        Item={"eventId": "full", "eventName": "Full", "eventDate": "2026-01-01", "availableSlots": 0}
    )
    dynamodb_tables["events"].put_item(
        Item={"eventId": "limited", "eventName": "Limited", "eventDate": "2026-01-02", "availableSlots": 2}
    )
    dynamodb_tables["events"].put_item(
        Item={"eventId": "open", "eventName": "Open", "eventDate": "2026-01-03", "availableSlots": 50}
    )
    handler = _load_handler()

    result = handler.handler({}, {})
    body = json.loads(result["body"])
    statuses = {e["eventId"]: e["status"] for e in body["events"]}
    assert statuses["full"] == "Full"
    assert statuses["limited"] == "Limited"
    assert statuses["open"] == "Available"


def test_list_events_empty(dynamodb_tables):
    handler = _load_handler()
    result = handler.handler({}, {})
    body = json.loads(result["body"])
    assert body["count"] == 0
    assert body["events"] == []
