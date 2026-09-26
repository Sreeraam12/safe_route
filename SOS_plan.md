# SafeRoute — SOS & Emergency Safety Feature
## Final Detailed Implementation Plan

> **Source of truth:** This plan merges the existing SafeRoute SOS architecture with the detailed SOS requirements reviewed from the project plan. It is intended to be the implementation reference for the SOS subsystem.

---

# 1. Objective

Add a complete SOS subsystem to SafeRoute that works during live navigation.

The SOS system should allow a user to:

1. Configure trusted contacts.
2. See an SOS button during live navigation.
3. Press the SOS button.
4. Explicitly confirm the action.
5. Create an SOS event.
6. Automatically capture the user's current GPS location.
7. Identify the current OSM road/segment.
8. Find the nearest mapped police station.
9. Notify the user's trusted contact(s).
10. Continue sharing the user's location while SOS is active.
11. Display the nearest police station to the user.
12. Provide a `Call 112` action.
13. Allow the user to cancel/resolve the SOS.
14. Store the SOS event in history.
15. Optionally create a safety-event signal associated with the road segment.

## Critical product boundaries

SafeRoute must **not** claim that police were notified unless an actual authorized police/emergency integration exists.

For the current implementation:

- Trusted contacts receive the actual notification.
- The nearest mapped police station is identified and displayed.
- The UI may provide a `Call 112` action.
- A single SOS must not automatically mark a road as permanently dangerous.
- SOS data must be handled as sensitive information.

---

# 2. Existing SafeRoute Components to Reuse

Do not create duplicate systems for functionality that already exists.

Reuse:

```text
Authentication
    ↓
Current logged-in user

Live Navigation
    ↓
Current GPS position
    ↓
Current route
    ↓
Current route segment
    ↓
Route progress
    ↓
Trip ID
```

The SOS subsystem should consume the existing navigation state.

The existing route/navigation system already knows:

```text
user
trip
route
current location
route progress
destination
```

Therefore:

**SOS must not independently create another navigation/GPS implementation.**

The same GPS/navigation state should be used for:

- Route progress
- Off-route detection
- Rerouting
- SOS activation
- Current road identification
- Live SOS location updates

---

# 3. Final SOS Architecture

```text
                         USER
                           │
                           ▼
                    LIVE NAVIGATION
                           │
           ┌───────────────┼────────────────┐
           │               │                │
          GPS            Route             Trip
           │             Progress           │
           │               │                │
           └───────────────┼────────────────┘
                           │
                           ▼
                       SOS BUTTON
                           │
                           ▼
                  CONFIRMATION MODAL
                           │
                    ┌──────┴──────┐
                    │             │
                   NO            YES
                    │             │
                  Close           ▼
                              SOS ENGINE
                                  │
                    ┌─────────────┼───────────────┐
                    │             │               │
                    ▼             ▼               ▼
                GPS Location  Current Road    Nearest Police
                              / Segment          Station
                    │             │               │
                    └─────────────┼───────────────┘
                                  ▼
                            CREATE SOS EVENT
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
              Trusted Contacts           Emergency UI
                     │                         │
                     ▼                         ▼
              SMS / Push Alert          SOS ACTIVE STATE
                                               │
                                               ▼
                                        Live Location Updates
                                               │
                                  ┌────────────┼────────────┐
                                  ▼            ▼            ▼
                               Cancel       Resolve      Call 112
```

---

# 4. Existing Database — Keep Intact

The current SafeRoute database already contains:

```text
users
trips
route_interactions
trip_feedback
personal_preferences
personal_segment_memory
personal_twin_state
```

## Existing tables: no SOS-related changes

| Existing table | Action |
|---|---|
| `users` | Keep unchanged |
| `trips` | Keep unchanged |
| `route_interactions` | Keep unchanged |
| `trip_feedback` | Keep unchanged |
| `personal_preferences` | Keep unchanged |
| `personal_segment_memory` | Keep unchanged initially |
| `personal_twin_state` | Keep unchanged |

The SOS system should connect to existing `users` and `trips` through relationships instead of adding unnecessary SOS columns.

Do **not** add an `sos_id` column to `trips`.

Instead:

```text
sos_events.trip_id → trips.id
```

---

# 5. New Database Tables

## Phase 1

Create:

```text
trusted_contacts
sos_events
sos_location_updates
sos_notifications
```

## Phase 2

Create:

```text
safety_events
```

---

# 6. `trusted_contacts`

The final recommended structure is:

```text
trusted_contacts
----------------
id
owner_user_id          → users.id
contact_user_id        → users.id, nullable
name
phone_number
relationship
is_verified
is_active
created_at
updated_at
```

## Why `contact_user_id` is nullable

### Case A — Contact is already a SafeRoute user

```text
owner_user_id   = User1
contact_user_id = User2
```

User2 can receive:

- Push notification
- In-app SOS alert
- Live location

### Case B — Contact is not a SafeRoute user

```text
owner_user_id   = User1
contact_user_id = NULL
phone_number    = User2's phone
```

User2 can receive:

- SMS
- Secure temporary location link

A trusted contact should not be forced to create a SafeRoute account just to receive an emergency alert.

## Relationship

```text
users.id
   │
   └── trusted_contacts.owner_user_id
```

A user can have multiple trusted contacts.

Recommended:

```text
Minimum: 1
Maximum: 3–5
```

---

# 7. Trusted Contact Registration / Onboarding

Trusted contacts should be part of the onboarding process, but existing users must not be broken by making them mandatory immediately.

## New user

```text
Create Account
      ↓
Personal Information
      ↓
Trusted Contacts
      ↓
Complete Registration
```

Example:

```text
Emergency Trusted Contact

Name
Phone Number
Relationship

[ + Add Another Contact ]

[ Continue ]
```

The user should explicitly consent to SafeRoute using these contacts for SOS notifications.

## Existing user

```text
Existing User
      ↓
Login
      ↓
If trusted contacts == 0
      ↓
Show setup prompt
      ↓
"Add trusted contacts for SOS"
```

Also provide:

```text
Profile
    ↓
Emergency & Safety
    ↓
Trusted Contacts
```

Existing users can:

- Add
- Edit
- Delete
- Verify
- Enable/disable contacts

For the development/demo environment, contacts may be seeded/updated manually if explicitly required. Production users should manage their own contacts.

---

# 8. Trusted Contact Verification

For a production-quality implementation, ideally verify the contact's phone number before using it for emergency notifications.

Possible future flow:

```text
Add Contact
    ↓
Send verification OTP
    ↓
Contact verified
    ↓
is_verified = true
```

For the college/demo version, this may initially be simplified if an SMS OTP provider is not being implemented.

However, keep:

```text
is_verified
```

in the database so verification can be added later.

---

# 9. Registration API Changes

Current:

```http
POST /api/auth/register
```

Possible request:

```json
{
  "name": "User",
  "email": "user@example.com",
  "password": "******",
  "trusted_contacts": [
    {
      "name": "Mother",
      "phone_number": "XXXXXXXXXX",
      "relationship": "Mother"
    }
  ]
}
```

Backend flow:

```text
Register User
      ↓
Create User
      ↓
Create Trusted Contacts
      ↓
Validate contacts
      ↓
Commit transaction
      ↓
Return registration success
```

Use a database transaction so registration does not leave partially-created user/contact data.

If trusted-contact creation fails, the registration transaction should be handled consistently rather than leaving orphaned contact records.

---

# 10. Profile / Emergency Settings UI

Add:

```text
Profile
├── Personal Information
├── Preferences
├── Personal Twin
├── Trip History
└── Emergency & Safety
```

Emergency & Safety:

```text
Emergency & Safety

Trusted Contacts

✓ Mother
  +91 XXXXX XXXXX
  Mother

✓ Friend
  +91 XXXXX XXXXX
  Friend

[ + Add Trusted Contact ]

[ Edit ]
[ Remove ]
```

Also show:

```text
SOS notifications will be sent to your active trusted contacts.
```

---

# 11. SOS Button Placement

The SOS button should be prominent **only during active navigation**.

Example:

```text
┌─────────────────────────────────────┐
│ Turn right in 180 m                 │
├─────────────────────────────────────┤
│                                     │
│               MAP                   │
│                                     │
│                📍                   │
│                                     │
├─────────────────────────────────────┤
│ ETA: 12 min       3.2 km remaining │
├─────────────────────────────────────┤
│                                     │
│           🚨 HOLD SOS               │
│                                     │
└─────────────────────────────────────┘
```

Prefer:

```text
Press and hold for 2–3 seconds
```

rather than a single accidental tap.

This reduces accidental emergency activation.

---

# 12. SOS Confirmation Modal

When the user presses SOS:

```text
┌─────────────────────────────────────┐
│        Create SOS Alert?            │
│                                     │
│ Are you sure you want to create     │
│ an SOS alert?                       │
│                                     │
│ Your trusted contacts will be       │
│ notified and your current location  │
│ will be shared.                     │
│                                     │
│ [ Cancel ]       [ Confirm SOS ]    │
└─────────────────────────────────────┘
```

The user must explicitly confirm.

---

# 13. SOS Activation API

Create:

```http
POST /api/sos/activate
```

Request can contain the current navigation state:

```json
{
  "trip_id": "trip-uuid",
  "latitude": 13.0827,
  "longitude": 80.2707,
  "accuracy": 8.2,
  "speed": 21.4,
  "heading": 90.0
}
```

The backend must obtain the authenticated user from the authentication token/session.

**Never trust a user-provided `user_id`.**

The current implementation can reuse the navigation state instead of asking the user to manually provide location.

---

# 14. SOS Activation Backend Flow

```text
POST /api/sos/activate
        ↓
Authenticate user
        ↓
Validate active trip
        ↓
Validate GPS coordinates
        ↓
Find current route segment
        ↓
Find nearest police station
        ↓
Create SOS event
        ↓
Load active trusted contacts
        ↓
Create notification records
        ↓
Send notifications
        ↓
Mark SOS ACTIVE
        ↓
Return emergency state
```

The backend is authoritative for SOS state.

---

# 15. `sos_events`

Main SOS record:

```text
sos_events
----------
id
user_id
trip_id
route_id
segment_id

latitude
longitude
gps_accuracy

road_name

nearest_police_station_name
nearest_police_station_latitude
nearest_police_station_longitude
nearest_police_station_distance_km

trigger_type
status

activated_at
resolved_at
resolution_type

created_at
updated_at
```

## `trigger_type`

Initial:

```text
MANUAL
```

Future:

```text
AUTOMATIC_CONFIRMATION
```

Do not implement automatic emergency activation unless the project explicitly adds a safe confirmation mechanism.

## `status`

```text
ACTIVE
CANCELLED
RESOLVED
```

## `resolution_type`

Recommended:

```text
USER_CANCELLED
TRIP_COMPLETED
USER_RESOLVED
SYSTEM_RESOLVED
```

---

# 16. `sos_location_updates`

Create:

```text
sos_location_updates
--------------------
id
sos_event_id
latitude
longitude
accuracy
speed
heading
timestamp
```

Purpose:

- Preserve the original SOS activation location in `sos_events`.
- Store subsequent movement in `sos_location_updates`.
- Allow trusted contacts to see live location.

Do not overwrite the original SOS coordinates every time GPS changes.

---

# 17. Location Update API

Recommended:

```http
POST /api/sos/{sos_id}/location
```

Flow:

```text
User1 GPS
    ↓
Navigation state
    ↓
SOS location update
    ↓
sos_location_updates
    ↓
Authorized trusted-contact view
```

Do not necessarily store every GPS point forever.

While SOS is active, use a reasonable update interval or meaningful movement threshold.

After SOS ends, retention should be limited according to the application's privacy policy.

---

# 18. Finding the Current Road

Reuse existing OSM route/map-matching functionality.

Do not create another independent road-matching system.

```text
GPS
 ↓
Existing map matching
 ↓
OSM nearest segment
```

Store:

```text
segment_id
road_name
latitude
longitude
```

with the SOS event.

---

# 19. Finding the Nearest Police Station

Use mapped OSM police-station data.

Query:

```text
amenity=police
```

Conceptually:

```text
Current GPS
      ↓
Nearby OSM police stations
      ↓
Calculate distance
      ↓
Sort by distance
      ↓
Nearest station
```

Example:

```json
{
  "name": "Example Police Station",
  "latitude": 13.05,
  "longitude": 80.28,
  "distance_km": 1.2
}
```

Important:

This identifies the nearest mapped police station. It does **not** guarantee that it is the operational jurisdiction responsible for the incident.

Do not query external OSM services excessively for every GPS update. Cache or refresh police-station data sensibly.

---

# 20. Police Notification Boundary

Because there is no authorized police-system integration in the current project:

**Never display:**

```text
Police have been notified
```

Instead:

```text
✓ SOS Alert Created
✓ Trusted contacts notified

Nearby police station identified:
Example Police Station
1.2 km away

[ Call 112 ]
[ View Location ]
```

The police station is informational.

---

# 21. 112 Integration

Add:

```text
[ Call 112 ]
```

The application may initiate the device's phone-call flow where supported.

The application must not falsely claim that the call was completed.

Possible UI:

```text
Emergency assistance

[ Call 112 ]
```

For the Chennai/Tamil Nadu implementation, 112 is the relevant integrated emergency helpline.

---

# 22. `sos_notifications`

Track each notification attempt:

```text
sos_notifications
-----------------
id
sos_event_id
trusted_contact_id
channel
status
sent_at
failure_reason
created_at
```

Possible channels:

```text
PUSH
SMS
EMAIL
```

Start with one reliable channel.

Possible statuses:

```text
PENDING
SENT
FAILED
```

This table allows retry and delivery-status tracking.

---

# 23. Notification Service

Do not hard-code notification logic inside the SOS API.

Create:

```text
notification_service.py
```

Responsibilities:

```text
send_sos_notification()
send_sos_location_update()
send_sos_resolved_notification()
```

Architecture:

```text
SOS Backend
     ↓
Notification Service
     ↓
Provider
     ↓
Trusted Contact
```

This makes the provider replaceable later.

---

# 24. Trusted Contact Notification

After SOS activation:

```text
SOS Backend
     ↓
Trusted Contacts
     ↓
Notification Service
```

Possible channels:

```text
SMS
Push Notification
Email
```

For the initial implementation, use one reliable channel first.

---

# 25. Registered SafeRoute Trusted Contact

If User2 is a SafeRoute user:

```text
User1
  ↓
SOS
  ↓
Backend
  ↓
User2
```

User2 can receive a push notification.

If User2 is logged in:

```text
🚨 SOS ALERT

User1 has activated an SOS.

Current location:
[Map]

Road:
Rajaji Salai, Chennai

[View Live Location]
```

If User2 is logged out:

```text
Push notification
      ↓
SafeRoute
      ↓
Authentication
      ↓
Authorized emergency view
```

A normal SafeRoute account must not automatically grant access to another user's emergency information.

---

# 26. External Trusted Contact

If the trusted contact is not a SafeRoute user:

```text
Backend
 ↓
SMS
 ↓
Secure temporary URL
```

The secure link must:

- Use a high-entropy random token.
- Not expose predictable user IDs.
- Expire.
- Stop working when the SOS is resolved/cancelled or the configured TTL expires.
- Provide only necessary emergency information.

Example message:

```text
🚨 SafeRoute SOS Alert

An SOS alert has been activated during navigation.

Current road:
Rajaji Salai, Chennai

Time:
7:42 PM

Current location:
[Open Location]

Nearby police station:
Example Police Station

Status:
SOS ACTIVE
```

Do not expose unnecessary personal information.

---

# 27. Live SOS Location Sharing

While SOS is active:

```text
User1 GPS
    ↓
sos_location_updates
    ↓
Notification / emergency-view system
    ↓
User2
    ↓
Live map
```

The registered trusted contact can view live location through an authorized SafeRoute emergency view.

An external contact can use the secure temporary web link.

The same navigation GPS should drive these updates.

---

# 28. SOS Active Screen

After successful activation:

```text
┌─────────────────────────────────────┐
│             🚨 SOS ACTIVE           │
│                                     │
│ Your trusted contacts have been     │
│ notified.                           │
│                                     │
│ Location sharing: ACTIVE            │
│                                     │
│ Current road: Rajaji Salai          │
│                                     │
│ Nearby police station:              │
│ Example Police Station              │
│ 1.2 km away                         │
│                                     │
│ [ Call 112 ]                        │
│ [ View Location ]                   │
│                                     │
│ [ Cancel SOS ]                      │
└─────────────────────────────────────┘
```

The map should remain visible if safe and technically appropriate.

---

# 29. SOS State Management

## Frontend state

```text
IDLE
 ↓
CONFIRMING
 ↓
ACTIVATING
 ↓
ACTIVE
 ↓
CANCELLING / RESOLVING
 ↓
RESOLVED
```

## Backend state

```text
ACTIVE
CANCELLED
RESOLVED
```

The backend is the authoritative state.

Do not rely only on frontend state.

---

# 30. Cancel SOS

Allow the user to cancel an accidental SOS.

Button:

```text
[ Cancel SOS ]
```

Confirmation:

```text
Cancel SOS?

Are you sure you want to cancel the active SOS alert?

[ Keep SOS Active ]
[ Cancel SOS ]
```

API:

```http
POST /api/sos/{sos_id}/cancel
```

Backend:

```text
ACTIVE
 ↓
CANCELLED
```

Trusted contacts should receive:

```text
SafeRoute SOS Update

The SOS alert has been cancelled by the user.

Status: CANCELLED
```

---

# 31. Resolve SOS

Support:

```http
POST /api/sos/{sos_id}/resolve
```

Use when the emergency has ended.

Only the authenticated owner or an authorized system role may resolve the SOS.

Possible resolution:

```text
ACTIVE
 ↓
RESOLVED
```

Send a resolution notification to trusted contacts.

Stop live SOS location updates after resolution.

---

# 32. SOS History

Add:

```text
Profile
 ↓
Emergency & Safety
 ↓
SOS History
```

Example:

```text
SOS History

23 Sep 2026
7:42 PM
Rajaji Salai
Status: Cancelled

12 Sep 2026
8:15 PM
Marina area
Status: Resolved
```

Avoid displaying complete historical GPS traces by default.

---

# 33. `safety_events` — Phase 2

Create:

```text
safety_events
-------------
id
sos_event_id
segment_id
latitude
longitude
event_type
created_at
status
confidence
expires_at
```

Example:

```text
event_type = USER_SOS
status = UNVERIFIED
```

A safety event is separate from the SOS event.

---

# 34. Never Automatically Mark a Road Dangerous

One SOS does not prove that an entire road is dangerous.

Never implement:

```text
SOS
 ↓
road risk = 100
```

Instead:

```text
SOS
 ↓
Safety Event
 ↓
UNVERIFIED
 ↓
Potential contextual signal
```

Repeated or verified signals can later contribute to a safety-event layer.

---

# 35. Temporary Safety Risk

If the research system eventually uses SOS events in route scoring:

```text
Base Risk
+
Crime
+
Environment
+
Traffic
+
Weather
+
Time
+
Verified Safety Events
```

A temporary event can have:

```text
created_at
expires_at
confidence
```

This prevents one SOS from permanently corrupting the road-risk model.

---

# 36. Personal Twin Integration

The SOS event should be linked to:

```text
user
trip
route
segment
```

But SOS should **not automatically change Personal Twin preferences**.

For example:

```text
SOS occurs
    ↓
Record event
```

does not automatically mean:

```text
user now hates this road
```

If the user later provides feedback such as:

```text
felt_unsafe = true
```

that can become a signal for Personal Twin learning.

Existing Personal Twin tables remain:

```text
personal_preferences
personal_segment_memory
personal_twin_state
```

No immediate SOS-specific columns are required.

---

# 37. Navigation Integration

During live navigation:

```text
Navigation state
├── current GPS
├── current segment
├── route progress
├── next instruction
├── ETA
└── SOS state
```

SOS consumes this existing state.

Do not create a second GPS tracking loop.

---

# 38. API Structure

## SOS

```http
POST /api/sos/activate
POST /api/sos/{sos_id}/location
POST /api/sos/{sos_id}/cancel
POST /api/sos/{sos_id}/resolve

GET /api/sos/active
GET /api/sos/history
GET /api/sos/{sos_id}
```

## Trusted Contacts

```http
GET    /api/emergency/contacts
POST   /api/emergency/contacts
PATCH  /api/emergency/contacts/{id}
DELETE /api/emergency/contacts/{id}
```

## Registration

Existing:

```http
POST /api/auth/register
```

should optionally accept trusted contacts as part of registration.

---

# 39. Backend File Structure

Extend the current backend:

```text
backend/app/
│
├── api/
│   ├── routes.py
│   ├── navigation.py
│   ├── trips.py
│   ├── auth.py
│   └── sos.py
│
├── services/
│   ├── navigation_engine.py
│   ├── gps_map_matcher.py
│   ├── rerouting_engine.py
│   ├── personal_twin_engine.py
│   ├── sos_engine.py
│   ├── notification_service.py
│   └── police_station_service.py
│
├── models/
│   ├── user.py
│   ├── trip.py
│   ├── twin.py
│   ├── trusted_contact.py
│   └── sos.py
│
└── schemas/
    ├── auth.py
    ├── navigation.py
    └── sos.py
```

---

# 40. Database Relationships

```text
USER
 │
 ├──────────────────┐
 │                  │
 ▼                  ▼
TRUSTED CONTACTS   TRIPS
                      │
                      ▼
                    SOS EVENTS
                      │
              ┌───────┴────────┐
              ▼                ▼
       SOS LOCATION       SAFETY EVENT
          UPDATES
```

More explicitly:

```text
User 1 → N TrustedContacts
User 1 → N Trips
User 1 → N SOS Events
Trip 1 → N SOS Events
SOS Event 1 → N LocationUpdates
SOS Event 1 → 0/1 SafetyEvent
```

`trusted_contacts.contact_user_id` is nullable to support both registered and external contacts.

---

# 41. Security Requirements

SOS is sensitive.

## Authentication

Every SOS API requires authentication.

## Ownership

A user can only:

```text
view own SOS
cancel own SOS
resolve own SOS
view own trusted contacts
modify own trusted contacts
```

A trusted contact can only view another user's emergency information through an authorized emergency-access flow.

## Input validation

Validate:

```text
latitude
longitude
accuracy
trip_id
contact IDs
sos_id
```

Do not trust client-provided `user_id`.

## Rate limiting

Prevent repeated SOS API abuse.

If an active SOS already exists:

```text
POST /api/sos/activate
```

should return the existing active SOS rather than creating duplicates.

## Audit logging

Record security-relevant events such as:

```text
SOS activated
SOS cancelled
SOS resolved
Trusted contact added
Trusted contact removed
Trusted contact updated
Notification attempted
```

Do not unnecessarily log sensitive information such as precise GPS coordinates or full phone numbers.

---

# 42. Notification Failure Handling

The SOS must still be created even if notification delivery fails.

Flow:

```text
SOS activated
      ↓
Create SOS
      ↓
SOS = ACTIVE
      ↓
Notification attempt
      ↓
Success / Failure
```

Never:

```text
notification failed
      ↓
SOS creation rolled back
```

Instead:

```text
sos_notifications
```

stores:

```text
id
sos_event_id
trusted_contact_id
channel
status
sent_at
failure_reason
```

Possible statuses:

```text
PENDING
SENT
FAILED
```

Failed notifications may be retried safely.

---

# 43. Network Failure During SOS

If the user loses network connectivity:

```text
SOS activation
      ↓
Network unavailable
```

Frontend should show:

```text
Unable to contact SafeRoute server.

Try again / Call 112
```

Do not falsely display:

```text
Trusted contacts notified
```

unless the backend confirms the notification request was successfully created/sent.

The emergency call option should remain available where supported.

The implementation should not fabricate an SOS record when the backend cannot be reached.

---

# 44. GPS Failure During SOS

If GPS accuracy is poor:

```text
GPS unavailable / poor accuracy
```

show:

```text
Location accuracy is currently low.
```

Use the latest valid location if available and clearly mark its age/accuracy.

Do not fabricate coordinates.

If the latest location is stale, expose that limitation in the emergency state.

---

# 45. Duplicate SOS Prevention

Prevent accidental repeated SOS creation.

If:

```text
ACTIVE SOS already exists
```

then:

```http
POST /api/sos/activate
```

should return the existing active SOS instead of creating duplicates.

Use a backend/database-level safeguard where appropriate, not only frontend state.

---

# 46. Privacy and Data Retention

SOS location is sensitive.

Implement appropriate retention rules for:

- `sos_events`
- `sos_location_updates`
- temporary emergency links
- notification metadata

Requirements:

- Stop live location sharing when SOS is resolved/cancelled.
- Expire temporary emergency links.
- Avoid unnecessary historical GPS display.
- Avoid unnecessary sensitive logging.
- Keep only the data required for safety, audit, research, or legally required purposes.
- Document retention policy in the application's privacy design.

---

# 47. Testing

## Registration

- New user can add trusted contacts.
- Multiple contacts work.
- Contact validation works.
- Registration transaction does not leave partial data.
- Existing user can add contacts later.
- User can skip contacts if allowed.
- Contact verification state works.

## Trusted Contacts

- Add contact.
- Edit contact.
- Delete contact.
- Enable/disable contact.
- Registered SafeRoute user can be associated.
- External contact can remain without `contact_user_id`.
- Unauthorized user cannot modify another user's contacts.

## SOS

- SOS button appears only during navigation.
- Press-and-hold works.
- Confirmation modal appears.
- Cancel works.
- Confirm creates one SOS.
- Duplicate activation does not create multiple active SOS events.
- Correct authenticated user is associated.

## GPS

- Current GPS is captured.
- Current road is identified.
- Current OSM segment is identified.
- Poor GPS accuracy is handled.
- Stale location is identified.
- No fabricated coordinates.

## Police Station

- Nearby mapped police station can be found.
- Distance is calculated.
- Police station information is displayed.
- No police notification is falsely claimed.
- External OSM queries are not made excessively.

## Notifications

- Trusted contacts receive alert.
- Multiple contacts receive alert.
- Registered contact receives appropriate in-app/push notification.
- External contact receives SMS/secure link.
- Notification failure is recorded.
- SOS remains active if one notification fails.
- Retry behavior works.
- Resolution notification is delivered.

## Live Location

- Location updates are created.
- Authorized trusted contact can view location.
- Unauthorized user cannot view it.
- Updates stop after SOS ends.
- Temporary location link expires.

## Cancellation

- User can cancel own SOS.
- Trusted contacts receive cancellation update.
- SOS history is updated.

## Resolution

- User can resolve own SOS.
- Trusted contacts receive resolution update.
- Active location sharing stops.

## Security

- User cannot access another user's SOS.
- User cannot modify another user's trusted contacts.
- Unauthorized SOS endpoints return appropriate errors.
- Rate limiting works.
- Sensitive information is not unnecessarily logged.

---

# 48. End-to-End Test

Test the complete flow:

```text
Register User
      ↓
Add Mother + Friend
      ↓
Login
      ↓
Search route
      ↓
Top 5 routes
      ↓
Select route
      ↓
Start live navigation simulation
      ↓
Move simulated GPS
      ↓
SOS button appears
      ↓
Press and hold SOS
      ↓
Confirmation
      ↓
Confirm
      ↓
Capture current GPS
      ↓
Identify current road
      ↓
Identify current OSM segment
      ↓
Find nearest police station
      ↓
Create SOS event
      ↓
Load trusted contacts
      ↓
Send notifications
      ↓
Show SOS ACTIVE
      ↓
Continue location updates
      ↓
Trusted contact views live location
      ↓
Cancel / resolve
      ↓
Send resolution update
      ↓
Stop location sharing
      ↓
Store history
```

---

# 49. Final UI Flow

## Registration

```text
Create Account
      ↓
Personal Details
      ↓
Trusted Contacts
      ↓
Add Contact
      ↓
Complete Registration
```

## Navigation

```text
Search
 ↓
Top 5 Routes
 ↓
Select Route
 ↓
Start Navigation
 ↓
Live Map
 ↓
🚨 SOS
```

## SOS

```text
SOS
 ↓
Create SOS Alert?
 ↓
Are you sure?
 ↓
Confirm
 ↓
SOS ACTIVE
 ↓
Trusted Contacts Notified
 ↓
Nearby Police Station Identified
 ↓
Call 112
 ↓
Live Location Sharing
 ↓
Cancel / Resolve
```

---

# 50. Important Product Boundaries

SafeRoute must explicitly distinguish:

## SOS

```text
User explicitly reports an emergency.
```

## ML Risk

```text
System estimates contextual road risk.
```

## Personal Twin

```text
System learns user-specific preferences and behavior.
```

## Police Station

```text
Nearest mapped police resource identified.
```

## Emergency Service

```text
Actual emergency communication only through authorized channels.
```

Never claim:

```text
ML detected a crime
```

or:

```text
Police were notified
```

unless those events actually occurred.

---

# 51. Recommended Implementation Order

Implement in this exact sequence.

## PHASE 1 — Trusted Contacts

```text
Trusted Contact database
        ↓
Trusted Contact API
        ↓
Registration integration
        ↓
Existing-user setup
        ↓
Verification support
```

## PHASE 2 — SOS Backend

```text
SOS database models
        ↓
SOS schemas
        ↓
SOS API
        ↓
Authentication/ownership
        ↓
Duplicate prevention
```

## PHASE 3 — Navigation Integration

```text
Reuse navigation GPS
        ↓
Current segment identification
        ↓
Nearest police station service
```

## PHASE 4 — SOS UI

```text
SOS button
        ↓
Press-and-hold
        ↓
Confirmation modal
        ↓
SOS active screen
```

## PHASE 5 — Notifications

```text
Notification service
        ↓
Trusted contact notification
        ↓
Notification status tracking
        ↓
Failure/retry handling
        ↓
Resolution notification
```

## PHASE 6 — Live SOS Location

```text
Live SOS location updates
        ↓
Authorized live-location view
        ↓
Location history/retention
        ↓
Stop tracking after resolution
```

## PHASE 7 — Cancel / Resolve

```text
Cancel
        ↓
Contact update
        ↓
Resolve
        ↓
SOS history
```

## PHASE 8 — Safety Event

```text
Safety Event
        ↓
Associate SOS with road segment
        ↓
Temporary/unverified safety signal
```

## PHASE 9 — 112

```text
112 call action
        ↓
Emergency UI
```

## PHASE 10 — Security & Privacy

```text
Authentication
        ↓
Ownership
        ↓
Rate limiting
        ↓
Audit logging
        ↓
Temporary-link security
        ↓
Location retention/privacy
```

## PHASE 11 — Full End-to-End Testing

Run the complete registration → navigation → SOS → notification → live location → resolution flow.

---

# 52. Final Database Structure

## Existing

```text
users
trips
route_interactions
trip_feedback
personal_preferences
personal_segment_memory
personal_twin_state
```

## New

```text
trusted_contacts
sos_events
sos_location_updates
sos_notifications
safety_events       ← Phase 2
```

## Relationships

```text
users
 │
 ├── trips
 │    │
 │    ├── route_interactions
 │    ├── trip_feedback
 │    └── sos_events
 │          │
 │          ├── sos_location_updates
 │          │
 │          ├── sos_notifications
 │          │       │
 │          │       └── trusted_contacts
 │          │
 │          └── safety_events
 │
 ├── trusted_contacts
 ├── personal_preferences
 ├── personal_segment_memory
 └── personal_twin_state
```

---

# 53. Final SafeRoute SOS Architecture

```text
                          SAFE ROUTE
                              │
                  ┌───────────┴───────────┐
                  │                       │
            ROUTE PLANNING          PERSONAL TWIN
                  │                       │
                  └───────────┬───────────┘
                              ▼
                         TOP 5 ROUTES
                              │
                              ▼
                       START NAVIGATION
                              │
                              ▼
                           LIVE GPS
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         Navigation        Risk Engine        SOS
              │               │               │
              │               │               ▼
              │               │         Confirmation
              │               │               │
              │               │               ▼
              │               │          SOS Event
              │               │               │
              │               │       ┌───────┴────────┐
              │               │       ▼                ▼
              │               │ Trusted Contacts   GPS/Segment
              │               │       │                │
              │               │       ▼                ▼
              │               │ Notifications    Nearby Police
              │               │                       │
              │               │                       ▼
              │               │                  Display Only
              │               │                       │
              │               │                  Call 112
              │               │
              └───────────────┼──────────────┐
                              ▼              │
                         Route Progress      │
                              │              │
                              ▼              │
                          Re-routing         │
                                             │
                              ┌──────────────┘
                              ▼
                         Trip Complete
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                 History            Feedback
                                        │
                                        ▼
                                  Personal Twin
```

---

# 54. Definition of Done

SOS is complete only when:

- Trusted contacts can be added during registration.
- Existing users can add trusted contacts later.
- Trusted contacts are stored securely in PostgreSQL.
- Registered and external trusted contacts are supported.
- Contact verification is architecturally supported.
- SOS button is visible during active navigation.
- SOS requires explicit confirmation.
- Current navigation GPS is reused.
- Current OSM road/segment is identified.
- Nearest mapped police station is found.
- SOS event is persisted.
- Trusted contacts are actually notified through the selected notification channel.
- Notification failures are tracked.
- Failed notifications do not delete the SOS event.
- SOS active state is shown.
- Live location updates work while SOS is active.
- Authorized trusted contacts can view the emergency location.
- Temporary emergency links are secure and expire.
- User can cancel/resolve SOS.
- Trusted contacts receive cancellation/resolution updates.
- SOS history is available.
- Nearby police station is displayed accurately.
- UI never falsely claims police were notified.
- `Call 112` is available.
- SOS can generate a safety-event record.
- One SOS does not automatically mark a road permanently high-risk.
- Authentication and ownership checks are enforced.
- Duplicate active SOS events are prevented.
- Network failures are handled safely.
- GPS failures/poor accuracy are handled safely.
- Audit events are recorded.
- Sensitive location data has appropriate retention/privacy handling.
- End-to-end SOS flow is tested.
