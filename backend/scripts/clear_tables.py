#!/usr/bin/env python3
"""
Deletes ALL items from the Events and Registrations DynamoDB tables.
Does NOT delete the tables themselves - just empties them.

Intended for dev/testing use before real registrations exist. Requires
explicit --yes confirmation to actually delete anything.

Usage:
    python scripts/clear_tables.py \
        --events-table event-ticketing-events-dev \
        --registrations-table event-ticketing-registrations-dev \
        --yes
"""
import argparse
import boto3


def clear_table(table, key_names):
    """Scan the whole table and delete every item found. Handles
    pagination and DynamoDB's batch_writer for efficient bulk deletes."""
    deleted = 0
    scan_kwargs = {}
    with table.batch_writer() as batch:
        while True:
            result = table.scan(**scan_kwargs)
            for item in result.get("Items", []):
                key = {k: item[k] for k in key_names}
                batch.delete_item(Key=key)
                deleted += 1
            if "LastEvaluatedKey" not in result:
                break
            scan_kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]
    return deleted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events-table", required=True)
    parser.add_argument("--registrations-table", required=True)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required flag to confirm you actually want to delete everything.",
    )
    args = parser.parse_args()

    if not args.yes:
        print("This will permanently delete ALL items from:")
        print(f"  - {args.events_table}")
        print(f"  - {args.registrations_table}")
        print("\nRe-run with --yes to confirm. Nothing was deleted.")
        return

    dynamodb = boto3.resource("dynamodb", region_name=args.region)

    events_table = dynamodb.Table(args.events_table)
    events_deleted = clear_table(events_table, key_names=["eventId"])
    print(f"Deleted {events_deleted} item(s) from {args.events_table}")

    registrations_table = dynamodb.Table(args.registrations_table)
    registrations_deleted = clear_table(
        registrations_table, key_names=["registrationId"]
    )
    print(f"Deleted {registrations_deleted} item(s) from {args.registrations_table}")

    print("\nDone. Both tables are now empty.")
    print("Run seed_events.py again if you want fresh demo data.")


if __name__ == "__main__":
    main()