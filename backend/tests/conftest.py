import os
import sys
import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "shared"))


@pytest.fixture
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_tables(aws_credentials):
    with mock_aws():
        os.environ["EVENTS_TABLE"] = "events-test"
        os.environ["REGISTRATIONS_TABLE"] = "registrations-test"

        client = boto3.resource("dynamodb", region_name="us-east-1")

        events_table = client.create_table(
            TableName="events-test",
            KeySchema=[{"AttributeName": "eventId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "eventId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        registrations_table = client.create_table(
            TableName="registrations-test",
            KeySchema=[{"AttributeName": "registrationId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "registrationId", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
                {"AttributeName": "registeredAt", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "emailIndex",
                    "KeySchema": [
                        {"AttributeName": "email", "KeyType": "HASH"},
                        {"AttributeName": "registeredAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield {"events": events_table, "registrations": registrations_table}
