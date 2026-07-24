# API Reference

Base URL (after deploy): `https://3yf8dopk35.execute-api.us-east-1.amazonaws.com/dev`

All responses are JSON. All endpoints support CORS (configured via `frontend_origin` Terraform variable — set to your actual frontend URL before production, `*` during development).

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Register for an event |
| `POST` | `/events` | Create a new event |
| `GET` | `/events` | List all events |
| `GET` | `/registrations/{email}` | View a participant's registrations |
| `DELETE` | `/registration/{id}` | Cancel a registration |

---

## POST /register

Register a participant for an event. Registering the same email for the same event twice is rejected — `registrationId` is deterministic per `(eventId, email)` pair, so re-registering after a cancellation reuses the same ID rather than creating a new one.

**Request body:**
```json
{
  "eventId": "aws-workshop-accra-2026",
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

**Success — 201:**
```json
{
  "registrationId": "9f86d081884c...",
  "eventId": "aws-workshop-accra-2026",
  "status": "confirmed"
}
```

**Errors:**
| Status | Meaning |
|---|---|
| 400 | Missing/invalid `eventId`, `email`, or `name` |
| 404 | `eventId` doesn't exist |
| 409 | Event is full (`availableSlots` is 0) |
| 409 | Already registered for this event with this email |
| 500 | Server error |

---

## POST /events

Create a new event. `eventId` defaults to a URL-safe slug of `eventName` (e.g. `"AWS Workshop Accra 2026"` → `"aws-workshop-accra-2026"`) unless you supply an explicit `eventId`. Creating an event with a name/ID that already exists is rejected — no duplicates.

**Request body:**
```json
{
  "eventName": "AWS Workshop Accra 2026",
  "eventDate": "2026-05-15",
  "location": "Accra, Ghana",
  "capacity": 50,
  "imageUrl": "https://your-bucket.s3.amazonaws.com/aws-workshop.jpg"
}
```
`eventName`, `eventDate`, and `capacity` are required. `location`, `imageUrl`, and an explicit `eventId` are optional. `imageUrl` must be a valid `http://` or `https://` URL if provided — intended for an S3-hosted event image, but any reachable image URL works.

**Success — 201:**
```json
{
  "eventId": "aws-workshop-accra-2026",
  "eventName": "AWS Workshop Accra 2026",
  "eventDate": "2026-05-15",
  "location": "Accra, Ghana",
  "capacity": 50,
  "availableSlots": 50,
  "imageUrl": "https://your-bucket.s3.amazonaws.com/aws-workshop.jpg"
}
```

**Errors:**
| Status | Meaning |
|---|---|
| 400 | Missing `eventName`, `eventDate`, or invalid `capacity` (must be a positive whole number) |
| 400 | `imageUrl` provided but not a valid http(s) URL |
| 409 | An event with this `eventId` already exists |
| 500 | Server error |

---

## GET /events

List all events with computed availability status.

**Success — 200:**
```json
{
  "count": 2,
  "events": [
    {
      "eventId": "aws-workshop-accra-2026",
      "eventName": "AWS Workshop Accra 2026",
      "eventDate": "2026-05-15",
      "availableSlots": 12,
      "status": "Available",
      "imageUrl": "https://your-bucket.s3.amazonaws.com/aws-workshop.jpg"
    },
    {
      "eventId": "cloud-solutions-summit",
      "eventName": "Cloud Solutions Summit",
      "eventDate": "2026-06-28",
      "availableSlots": 3,
      "status": "Limited"
    }
  ]
}
```

`status` is computed server-side: `Full` (0 slots), `Limited` (1-5 slots), `Available` (6+ slots). `imageUrl` is omitted entirely if the event was created without one — don't assume it's always present.

---

## GET /registrations/{email}

View all registrations for a given email, most recent first.

**Example:** `GET /registrations/jane@example.com`

**Success — 200:**
```json
{
  "email": "jane@example.com",
  "registrations": [
    {
      "registrationId": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
      "eventId": "aws-workshop-accra-2026",
      "email": "jane@example.com",
      "name": "Jane Doe",
      "status": "confirmed",
      "registeredAt": "2026-07-21T10:30:00+00:00"
    }
  ]
}
```

Returns `{ "registrations": [] }` (200) if none found — not a 404.

**Errors:**
| Status | Meaning |
|---|---|
| 400 | Invalid email format in path |
| 500 | Server error |

---

## DELETE /registration/{id}

Cancel a registration. Soft-delete — sets `status` to `cancelled` and restores the event's `availableSlots` by 1.

**Example:** `DELETE /registration/9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08`

**Success — 200:**
```json
{
  "registrationId": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "status": "cancelled"
}
```

**Errors:**
| Status | Meaning |
|---|---|
| 400 | Missing id in path |
| 404 | Registration not found |
| 409 | Already cancelled |
| 500 | Server error |

---

## Notes for the frontend team

- No auth is implemented yet (public endpoints) — let the backend team know if you need an API key or Cognito auth added before going live.
- Email is lowercased and trimmed server-side before storage/lookup, so lookups are case-insensitive.
- Rate limit: 10 requests/sec sustained, burst of 20, per the API Gateway stage throttle settings.
- `registrationId` is a deterministic hash (64 hex characters, not a UUID) derived from `(eventId, email)` — treat it as an opaque string either way, but don't assume UUID format if you're validating it client-side.
- `eventId` is a URL-safe slug by default (e.g. `aws-workshop-accra-2026`), not a UUID — safe to use directly in URLs without encoding.
- Registering the same email for the same event twice now returns `409` on the second attempt (previously this was a bug and silently succeeded) — build your UI to handle that as "you're already registered," not a generic error.