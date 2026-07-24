import json
import os
import sys
import importlib.util

_HANDLER_PATH = os.path.join(os.path.dirname(__file__), "..", "lambda", "create_event", "handler.py")
_SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "lambda", "shared")


def _load_handler():
    if _SHARED_DIR not in sys.path:
        sys.path.insert(0, _SHARED_DIR)
    spec = importlib.util.spec_from_file_location("create_event_handler", _HANDLER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_create_event_success(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps(
        {
            "eventName": "AWS Workshop Accra 2026",
            "eventDate": "2026-05-15",
            "location": "Accra, Ghana",
            "capacity": 50,
            "imageUrl": "https://example-bucket.s3.amazonaws.com/aws-workshop.jpg",
        }
    )
    result = handler.handler({"body": body}, {})

    assert result["statusCode"] == 201
    created = json.loads(result["body"])
    assert created["eventId"] == "aws-workshop-accra-2026"
    assert created["availableSlots"] == 50
    assert created["imageUrl"] == "https://example-bucket.s3.amazonaws.com/aws-workshop.jpg"

    stored = dynamodb_tables["events"].get_item(
        Key={"eventId": "aws-workshop-accra-2026"}
    )["Item"]
    assert stored["eventName"] == "AWS Workshop Accra 2026"


def test_create_event_duplicate_rejected(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps(
        {"eventName": "Cloud Summit", "eventDate": "2026-06-28", "capacity": 20}
    )

    first = handler.handler({"body": body}, {})
    assert first["statusCode"] == 201

    second = handler.handler({"body": body}, {})
    assert second["statusCode"] == 409
    assert "already exists" in json.loads(second["body"])["error"].lower()


def test_create_event_missing_name(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps({"eventDate": "2026-06-28", "capacity": 20})
    result = handler.handler({"body": body}, {})
    assert result["statusCode"] == 400


def test_create_event_missing_date(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps({"eventName": "No Date Event", "capacity": 20})
    result = handler.handler({"body": body}, {})
    assert result["statusCode"] == 400


def test_create_event_invalid_capacity(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps(
        {"eventName": "Bad Capacity", "eventDate": "2026-06-28", "capacity": 0}
    )
    result = handler.handler({"body": body}, {})
    assert result["statusCode"] == 400


def test_create_event_invalid_image_url(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps(
        {
            "eventName": "Bad Image",
            "eventDate": "2026-06-28",
            "capacity": 10,
            "imageUrl": "not-a-url",
        }
    )
    result = handler.handler({"body": body}, {})
    assert result["statusCode"] == 400


def test_create_event_explicit_id_overrides_slug(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps(
        {
            "eventId": "custom-id-123",
            "eventName": "Custom ID Event",
            "eventDate": "2026-06-28",
            "capacity": 10,
        }
    )
    result = handler.handler({"body": body}, {})
    assert result["statusCode"] == 201
    assert json.loads(result["body"])["eventId"] == "custom-id-123"


def test_create_event_without_image_url_is_optional(dynamodb_tables):
    handler = _load_handler()
    body = json.dumps(
        {"eventName": "No Image Event", "eventDate": "2026-06-28", "capacity": 10}
    )
    result = handler.handler({"body": body}, {})
    assert result["statusCode"] == 201
    created = json.loads(result["body"])
    assert "imageUrl" not in created