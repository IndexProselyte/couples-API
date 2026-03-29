# API Requirements — Couples Together App

> **Purpose:** Exact specification for a Python backend serving this Flutter app.
> All endpoint paths, HTTP methods, request bodies, and response shapes are derived
> directly from the live client code. Implement these exactly — the app will not work
> if they differ.
>
> **Legend:**
> - ✅ **Wired** — the app already calls this endpoint; implement it first
> - 🔜 **Planned** — code stub exists; endpoint not yet called from the UI
> - ❌ **Not implemented** — app has no client code yet; can be added later

---

## App Overview

A private **two-person** mobile app (Flutter) for a couple.
Navigation: `Login → AppShell` with 3 tabs: **Dashboard**, **Chat**, **Timeline**.
Settings accessible from Dashboard.

One user is "yours" (pink theme), the other "partner" (blue theme).
Every endpoint is implicitly scoped to **this couple only** — no multi-user feeds,
no public accounts.

---

## Infrastructure

### Base URL

Configured by the user in Settings, stored in `SharedPreferences` under key
`server_url`. All paths below are relative to that base.

```
GET  /health    (optional liveness probe)
```

### Authentication

The app reads `SharedPreferences['auth_token']` and injects it automatically:

```
Authorization: Bearer <token>
```

**Login is not wired to an API yet (❌).** The login page currently validates a
local secret without contacting the server. When implemented, the token must be
saved to `SharedPreferences['auth_token']`.

```
❌  POST /auth/login
    Body:    { "password": string }
    Returns: { "token": string, "user_id": string, "role": "hers" | "his" }

❌  POST /auth/logout
    Headers: Authorization: Bearer <token>
    Returns: { "ok": true }
```

> `role` determines which partner is "you" vs "partner" — drives bubble alignment
> in chat, whose mood/name is shown where, etc.

---

## 1. Couple Profile  ✅

### GET /couple/profile

Called on every Dashboard load (background sync after prefs cache renders).

**Response — all fields required:**

```json
{
  "start_date":         "YYYY-MM-DD",
  "your_name":          "string",
  "partner_name":       "string",
  "couple_photo_url":   "https://…" | null,
  "partner_avatar_url": "https://…" | null
}
```

`start_date` is an ISO 8601 date string (`DateTime.parse()` is called on it).

### PUT /couple/profile

Called when the user changes their relationship start date in Settings.
Body is a **partial** object — only the fields being updated are sent.

```json
{
  "start_date":    "YYYY-MM-DD",
  "your_name":     "string",
  "partner_name":  "string"
}
```

Response is ignored by the client (fire-and-forget). Return anything 2xx.

> **Note:** Photo upload is not yet wired (❌). `couple_photo_url` and
> `partner_avatar_url` come back in `GET /couple/profile` as server-hosted URLs.

---

## 2. Moods  ✅

Mood values the client sends and expects back:

| API string | UI label |
|------------|----------|
| `happy`    | Happy    |
| `in_love`  | In Love  |
| `sad`      | Sad      |
| `tired`    | Tired    |
| `excited`  | Excited  |
| `neutral`  | Neutral  |

### GET /mood

Called on every Dashboard load (alongside profile fetch, in parallel).

**Response — exact structure required:**

```json
{
  "your_mood":     { "value": "happy" },
  "partner_mood":  { "value": "in_love" }
}
```

> The nested `{"value": "..."}` wrapper is required — the client reads
> `j['your_mood']['value']`.

### PUT /mood

Called when the user picks their mood. Fire-and-forget.

```json
{ "mood": "in_love" }
```

Response is ignored. Return anything 2xx.

---

## 3. Chat Messages  ✅

### GET /messages

Called on every Chat page load (background sync after local cache renders).

**Query params:**

| Param   | Type | Default | Description                      |
|---------|------|---------|----------------------------------|
| `limit` | int  | 100     | Maximum messages to return       |
| `before`| str  | —       | Cursor for pagination (optional) |

**Response — messages wrapped in object:**

```json
{
  "messages": [
    {
      "id":               "string",
      "text":             "string",
      "is_sent":          true,
      "time":             "HH:mm",
      "date":             "YYYY-MM-DD",
      "is_file":          false,
      "file_name":        null,
      "file_size":        null,
      "image_url":        null,
      "sticker_path":     null,
      "reactions":        [],
      "is_starred":       false,
      "is_voice":         false,
      "voice_duration_ms": null,
      "voice_waveform":   null,
      "reply_to_text":    null,
      "reply_to_is_sent": null
    }
  ]
}
```

> `is_sent` is from the perspective of the **authenticated user**.
> The server should derive this from `sender_id == authenticated_user_id`.
> `date` is only set on the first message of a new calendar day (used as day
> separator in the UI) — omit it or set `null` for messages on the same day
> as the previous one.

### POST /messages

Called when the user sends a text message (or a message with a reply context).

**Request body:**

```json
{
  "text":             "string",
  "reply_to_id":      "string | absent",
  "reply_to_text":    "string | absent",
  "reply_to_is_sent": "bool | absent"
}
```

**Response — the created message (same shape as GET item above):**

```json
{
  "id":       "server-assigned-string",
  "text":     "string",
  "is_sent":  true,
  "time":     "HH:mm",
  "date":     "YYYY-MM-DD | null",
  ...
}
```

> The client writes the returned `id` back to the local message so subsequent
> reaction/star/delete calls can use it.

> **Media messages** (images, files, stickers, voice) are **not yet wired** (🔜).
> A generic `POST /upload` endpoint is planned. Until then the client stores
> images as local file paths and doesn't send them to the server.

### PUT /messages/{id}/reactions

Called when the user taps a reaction emoji.

```json
{ "emoji": ":3", "action": "add" }
```

`action` is `"add"` or `"remove"`.

**Response — updated reactions list:**

```json
{ "reactions": [":3", ":D"] }
```

The client replaces the local reactions array with this returned value.

### PUT /messages/{id}/star

Called when the user stars or unstars a message.

```json
{ "starred": true }
```

Response is ignored. Return anything 2xx.

### DELETE /messages/{id}

Called when the user deletes a message. Response is ignored.

---

## 4. Timeline Events  ✅

### GET /timeline/events

Called on every Timeline page load (background sync after local cache renders).

**Query params (optional, for future use):**

| Param | Description          |
|-------|----------------------|
| `year`| Filter by event year |
| `tag` | Filter by tag        |

**Response — events wrapped in object:**

```json
{
  "events": [
    {
      "id":         "string",
      "title":      "string",
      "date":       1699999999000,
      "canvas":     [...],
      "stickers":   [...],
      "tags":       ["vacation"],
      "location":   "Paris" | null,
      "dot_color":  4294198442 | null,
      "line_color": 4294198442 | null,
      "card_color": 4294198442 | null,
      "is_pinned":  false
    }
  ]
}
```

> `date` is **epoch milliseconds** (integer), not ISO 8601.
> Colors are **ARGB integers** (e.g. `0xFFE07AAA` = `4294198442`).
> Return events sorted by `date` ascending.

### POST /timeline/events

Called when the user saves a new timeline event.

**Request body — same shape as GET item, without `id`:**

```json
{
  "title":      "Our first trip",
  "date":       1699999999000,
  "canvas":     [...],
  "stickers":   [],
  "tags":       ["travel"],
  "location":   "Paris",
  "dot_color":  null,
  "line_color": null,
  "card_color": null,
  "is_pinned":  false
}
```

**Response — the `id` the server assigned (only `id` is read by the client):**

```json
{ "id": "server-assigned-string" }
```

The server may return the full event; only `id` is used.

### PUT /timeline/events/{id}

Called when the user edits an event, changes its colour, pins/unpins it.
Body is the **full** updated event (same shape as POST body above, without `id`).

Response is ignored. Return anything 2xx.

### DELETE /timeline/events/{id}

Called when the user confirms event deletion. Response is ignored.

---

## 5. Canvas Block Schema

Timeline events contain a `canvas` array. Each element is a **CanvasBlock**:

```json
{
  "content": { ... },
  "x":        0.0,
  "y":        0.0,
  "w":        1080.0,
  "h":        160.0,
  "rotation": 0.0
}
```

`content` is a discriminated union on `type`:

```json
{ "type": "text",    "text": "...", "censored": false, "fontFamily": null, "fontWeight": null, "fontSize": null }
{ "type": "image",   "path": "https://…", "censored": false, "title": null, "height": null }
{ "type": "collage", "paths": ["https://…"], "layout": "bigLeft", "censored": false }
{ "type": "video",   "path": "https://…", "censored": false, "height": null }
{ "type": "polaroid","path": "https://…", "caption": "", "rotation": 0.0, "censored": false }
{ "type": "quote",   "text": "...", "attribution": "" }
{ "type": "washi",   "color": 4294951365, "style": "solid", "rotation": 0.0 }
{ "type": "divider", "style": "line" }
{ "type": "doodle",  "strokes": [[{"x":0,"y":0}]], "color": 4293500044, "strokeWidth": 3.0 }
```

> `path` values in `image`, `collage`, `video`, `polaroid` are currently **local
> filesystem paths** on the device. When file upload (`POST /upload`) is
> implemented, they will become server-hosted URLs. Store them as strings.
>
> `censored` is a local display toggle (blurs content); store as-is.

---

## 6. Event Stickers

```json
{
  "path":     "assets/stickers/hamster/0-1.thumb128.png",
  "x":        0.5,
  "y":        0.3,
  "size":     64.0,
  "rotation": -5.0
}
```

Sticker paths are Flutter asset references bundled in the app — they are **not
uploaded**, just stored as strings.

---

## 7. Not Yet Wired  ❌ / 🔜

These endpoints are planned but have **no client code** calling them yet.
They do not need to block the initial backend release, but must be added before
the app is feature-complete.

### POST /upload  🔜

Generic file upload for images/videos in chat and timeline.

```
POST /upload
Body: multipart/form-data  { "file": <binary> }
Returns: { "url": "https://cdn.example.com/uploads/abc123.jpg" }
```

### GET /integrations/status  🔜

Chat has a side drawer showing partner's presence on external services.
Currently hardcoded; will call this endpoint once wired.

```json
{
  "discord":   { "status": "online | offline | dnd",            "detail": "string" },
  "instagram": { "status": "online | offline",                  "detail": "string" },
  "steam":     { "status": "online | playing | offline",        "detail": "string" },
  "spotify":   { "status": "online | offline",                  "detail": "string", "track": "string | absent" }
}
```

### WebSocket /ws  🔜

Real-time channel for new messages and typing indicator.

```
WS /ws?token=<jwt>   (or Authorization header on upgrade)

Server → Client:
  { "type": "message",        "data": <ChatMessage> }
  { "type": "message_update", "data": { "id": "...", "reactions": [...], "is_starred": bool } }
  { "type": "message_delete", "data": { "id": "..." } }
  { "type": "partner_typing", "data": { "typing": bool } }

Client → Server:
  { "type": "typing", "data": { "typing": bool } }
```

### POST /auth/login  ❌

```json
{ "password": "string" }
```

```json
{ "token": "string", "user_id": "string", "role": "hers" | "his" }
```

The `token` must be saved to `SharedPreferences['auth_token']`.

### DELETE /user/data  ❌

```json
{ "type": "chat" | "timeline" | "all" }
```

### GET /timeline/cover  /  POST /timeline/cover  ❌

```
GET /timeline/cover → { "url": "string | null" }
POST /timeline/cover — multipart { "file": <binary> } → { "url": "string" }
```

### POST /notifications/send  ❌

```json
{
  "text":         "string",
  "image_url":    "string | null",
  "scheduled_for": "ISO8601 | \"now\""
}
```

---

## 8. SharedPreferences Reference

These are all keys the client reads/writes locally. Listed for context; most are
synced to the server via the endpoints above.

| Key                    | Type             | Populated by                    |
|------------------------|------------------|---------------------------------|
| `server_url`           | String           | Settings page (user input)      |
| `auth_token`           | String           | Login (once wired)              |
| `relationship_start`   | String (ISO8601) | `GET /couple/profile`           |
| `your_name`            | String           | `GET /couple/profile`           |
| `partner_name`         | String           | `GET /couple/profile`           |
| `api_couple_photo_url` | String           | `GET /couple/profile`           |
| `api_partner_avatar_url`| String          | `GET /couple/profile`           |
| `cached_your_mood`     | String           | `GET /mood`                     |
| `cached_partner_mood`  | String           | `GET /mood`                     |
| `chat_messages_v1`     | List\<String\>   | `GET /messages`                 |
| `timeline_events_v1`   | String (JSON)    | `GET /timeline/events`          |
| `couple_photo`         | String (path)    | Local gallery pick              |
| `partner_avatar`       | String (path)    | Local gallery pick              |
| `custom_quotes`        | List\<String\>   | Local only                      |
| `last_confetti_day`    | int              | Local only                      |
| `timeline_cover`       | String (path)    | Local gallery pick              |
| `theme_variant`        | int              | Settings page (0–3)             |
| `dark_mode`            | bool             | Settings page                   |
| `theme_is_hers`        | bool             | Settings page                   |

---

## 9. Consolidated Endpoint List

```
✅ Wired — implement these first:

  GET    /couple/profile
  PUT    /couple/profile

  GET    /mood
  PUT    /mood

  GET    /messages?limit={int}[&before={id}]
  POST   /messages
  PUT    /messages/{id}/reactions
  PUT    /messages/{id}/star
  DELETE /messages/{id}

  GET    /timeline/events[?year={int}][&tag={str}]
  POST   /timeline/events
  PUT    /timeline/events/{id}
  DELETE /timeline/events/{id}

🔜 Planned — stub these out:

  POST   /upload
  GET    /integrations/status
  WS     /ws

❌ Not wired yet — can wait:

  POST   /auth/login
  POST   /auth/logout
  POST   /notifications/send
  GET    /timeline/cover
  POST   /timeline/cover
  DELETE /user/data
```

---

## 10. Design Notes for the Backend

1. **Two users max.** No ACL complexity — both users in a couple share all data.

2. **`is_sent` is always from the authenticated user's perspective.** Store `sender_id`
   internally; compute `is_sent = (sender_id == authenticated_user_id)` on the way out.

3. **Sticker paths are Flutter asset paths** (`assets/stickers/hamster/…`). Store
   as strings; the app renders them via `Image.asset()`. Do not treat as uploads.

4. **Timeline `date` is epoch milliseconds**, not ISO 8601. Dart's `DateTime`
   stores and parses it with `.millisecondsSinceEpoch`.

5. **Colors are ARGB integers.** Dart's `Color.value` gives a 32-bit int such as
   `0xFFE07AAA` = `4294198442`.

6. **All mutations are fire-and-forget on the client.** The app updates local state
   immediately and calls the API in the background. Server errors are silently
   ignored. This means the server does not need to return rich error bodies for
   mutation endpoints — any non-2xx response is just dropped.

7. **`GET /messages` must wrap its array** in `{ "messages": [...] }` — the client
   reads `j['messages']`.

8. **`GET /timeline/events` must wrap its array** in `{ "events": [...] }` — the
   client reads `j['events']`.

9. **Mood GET response must nest** under `your_mood.value` / `partner_mood.value` —
   the client reads `j['your_mood']['value']`.

10. **`POST /timeline/events` only needs to return `{ "id": "..." }`** — the client
    only reads the `id` field from the response.
