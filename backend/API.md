# API Reference

Base URL (after deploy): `https://3yf8dopk35.execute-api.us-east-1.amazonaws.com/dev`

All responses are JSON. All endpoints support CORS (configured via `frontend_origin` Terraform variable — set to your actual frontend URL before production, `*` during development).

---

## POST /register

Register a participant for an event.

**Request body:**
```json
{
  "eventId": "evt-aws-workshop-2026",
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

**Success — 201:**
```json
{
  "registrationId": "a1b2c3d4-...",
  "eventId": "evt-aws-workshop-2026",
  "status": "confirmed"
}
```

**Errors:**
| Status | Meaning |
|---|---|
| 400 | Missing/invalid `eventId`, `email`, or `name` |
| 404 | `eventId` doesn't exist |
| 409 | Event is full (`availableSlots` is 0) |
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
      "eventId": "evt-aws-workshop-2026",
      "eventName": "AWS Workshop Accra 2026",
      "eventDate": "2026-05-15",
      "availableSlots": 12,
      "status": "Available"
    },
    {
      "eventId": "evt-cloud-summit-2026",
      "eventName": "Cloud Solutions Summit",
      "eventDate": "2026-06-28",
      "availableSlots": 3,
      "status": "Limited"
    }
  ]
}
```

`status` is computed server-side: `Full` (0 slots), `Limited` (1-5 slots), `Available` (6+ slots).

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
      "registrationId": "a1b2c3d4-...",
      "eventId": "evt-aws-workshop-2026",
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

**Example:** `DELETE /registration/a1b2c3d4-...`

**Success — 200:**
```json
{
  "registrationId": "a1b2c3d4-...",
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
