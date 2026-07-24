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
        "eventId": "aws-workshop-accra-2026",
        "eventName": "AWS Workshop Accra 2026",
        "eventDate": "2026-05-15",
        "location": "Accra, Ghana",
        "capacity": 50,
        "availableSlots": 50,
        "imageUrl": "https://source.unsplash.com/featured/800x600/?aws,cloud",
    },
    {
        "eventId": "cloud-solutions-summit",
        "eventName": "Cloud Solutions Summit",
        "eventDate": "2026-06-28",
        "location": "Accra, Ghana",
        "capacity": 30,
        "availableSlots": 4,
        "imageUrl": "https://source.unsplash.com/featured/800x600/?cloud,technology",
    },
    {
        "eventId": "devops-days-ghana",
        "eventName": "DevOps Days Ghana",
        "eventDate": "2026-07-10",
        "location": "Kumasi, Ghana",
        "capacity": 120,
        "availableSlots": 75,
        "imageUrl": "https://source.unsplash.com/featured/800x600/?devops,server",
    },
    {
        "eventId": "ai-innovation-summit",
        "eventName": "AI Innovation Summit",
        "eventDate": "2026-07-25",
        "location": "Accra, Ghana",
        "capacity": 200,
        "availableSlots": 180,
        "imageUrl": "https://source.unsplash.com/featured/800x600/?artificial-intelligence",
    },
    {
        "eventId": "cybersecurity-conference",
        "eventName": "Cybersecurity Conference",
        "eventDate": "2026-08-08",
        "location": "Takoradi, Ghana",
        "capacity": 80,
        "availableSlots": 24,
        "imageUrl": "https://source.unsplash.com/featured/800x600/?cybersecurity,hacker",
    },
    {
        "eventId": "python-developers-meetup",
        "eventName": "Python Developers Meetup",
        "eventDate": "2026-08-20",
        "location": "Cape Coast, Ghana",
        "capacity": 60,
        "availableSlots": 18,
        "imageUrl": "https://source.unsplash.com/featured/800x600/?python,programming",
    }
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