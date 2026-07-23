#!/usr/bin/env python3
"""
Seeds demo events into the Events DynamoDB table so the frontend team
has real data to build against.

Usage:
    python scripts/seed_events.py --table event-ticketing-events-dev
"""
import argparse
import boto3


DEMO_EVENTS = [
    {
        "eventId": "evt-aws-workshop-2026",
        "eventName": "AWS Workshop Accra 2026",
        "eventDate": "2026-05-15",
        "location": "Accra, Ghana",
        "capacity": 50,
        "availableSlots": 50,
    },
    {
        "eventId": "evt-cloud-summit-2026",
        "eventName": "Cloud Solutions Summit",
        "eventDate": "2026-06-28",
        "location": "Accra, Ghana",
        "capacity": 30,
        "availableSlots": 4,
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True, help="Events DynamoDB table name")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    dynamodb = boto3.resource("dynamodb", region_name=args.region)
    table = dynamodb.Table(args.table)

    for event in DEMO_EVENTS:
        table.put_item(Item=event)
        print(f"Seeded: {event['eventName']} ({event['eventId']})")

    print(f"\nDone. {len(DEMO_EVENTS)} events seeded into '{args.table}'.")


if __name__ == "__main__":
    main()
