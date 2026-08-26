# cc-watcher — Cinema City ticket watcher (CZ)

Cinema City showtime watcher for the Czech Republic, initially configured for
the IMAX auditorium at Cinema City Praha Flora. It monitors ticket availability
for selected films and sends email notifications when matching screenings or
new seats become available.

## How it works

Cinema City exposes an unofficial public JSON API for showtime data—the same API
used by its website. The base URL for the Czech tenant (`10101`) is:

```text
https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/
```

The main endpoints are regular `GET` requests and require no authentication:

| Endpoint                                                                 | Description                                                     |
| ------------------------------------------------------------------------ | --------------------------------------------------------------- |
| `cinemas/with-event/until/{YYYY-MM-DD}?attr=&lang=cs_CZ`                 | Lists cinemas with events; Praha Flora has ID `1052`            |
| `films/until/{YYYY-MM-DD}?attr=&lang=cs_CZ`                              | Lists films; for example, _Odyssea_ has ID `7268s2r`            |
| `film-events/in-cinema/{cinemaId}/at-date/{YYYY-MM-DD}?attr=&lang=cs_CZ` | Returns films and screenings for a cinema on a specific date    |
| `dates/in-cinema/{cinemaId}/until/{YYYY-MM-DD}?attr=70-mm&lang=cs_CZ`    | Returns dates with matching screenings in a single request      |
| `attributes?lang=cs_CZ`                                                  | Returns the complete attribute catalogue used by `attributeIds` |

The `attr` filter is applied server-side, but multiple values are often combined
using **OR**, not **AND**. The watcher therefore sends one attribute to the API
to narrow the result set and applies any remaining filters locally. Using the
`dates/...` endpoint with `attr=70-mm` reduces a typical scan from approximately
46 requests to approximately 6.

## Testing the API with Postman

Start with these three requests. They require no headers or authentication:

```http
GET https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/dates/in-cinema/1052/until/2026-09-30?attr=70-mm&lang=cs_CZ
GET https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/film-events/in-cinema/1052/at-date/2026-08-01?attr=70-mm&lang=cs_CZ
GET https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/attributes?lang=cs_CZ
```

In the second response, inspect the following fields in `body.events[]`:
`soldOut`, `availabilityRatio`, `auditorium`, and
`bookingRouterLaunchLink`. These fields provide all the information needed by
the watcher:

- `soldOut` indicates whether the screening is sold out.
- `availabilityRatio` represents the proportion of available seats, with a
  resolution of approximately one seat.
- `attributeIds` contains screening attributes such as `70-mm` for 70 mm
  screenings in the `IMAX VOLVO` auditorium.
- `bookingRouterLaunchLink` provides a working direct link to ticket sales:

  ```text
  https://www.cinemacity.cz/cz/booking-router/launch/{eventId}?lang=cs
  ```

The `bookingLink` field, which points to
`tickets.cinemacity.cz/api/order/...`, is obsolete and returns HTTP 404. It also
appears as `obsoleteBookingUrl` inside `compositeBookingLink`. The current
booking system uses `tickets.rel.cinemacity.cz`.

## Detection rules

The watcher detects three types of events:

1. **New screening** — a matching screening appears for the first time, for
   example after the weekly schedule is published.
2. **Tickets available again** — a screening changes from `soldOut=true` to
   `soldOut=false`.
3. **More seats available** — `availabilityRatio` increases by at least the
   configured threshold, which defaults to approximately one seat.

Seat increases are calculated relative to the most recently stored state.
Seats that have always been available, such as wheelchair-accessible spaces,
therefore do not cause repeated false alarms; only an actual change triggers an
alert.

The first run only initializes the state and does not send alerts. All events
detected during a single run are grouped into one email. A cooldown is applied
separately to each screening and alert type.

## When tickets are released

Research indicates that tickets are usually released **on Tuesday mornings**,
not on Wednesdays. Czech cinemas schedule their cinema week from Thursday
through Wednesday, and sales for the following week generally open on the
preceding Tuesday morning. The exact time is not publicly documented, so the
intensive polling window should start at approximately 06:30. The usual sales
horizon is approximately one week.

Praha Flora is one of three cinemas in the European Union capable of genuine
15/70 mm projection, alongside cinemas in Brussels and Montpellier. Its `IMAX
VOLVO` auditorium has an estimated capacity of **385 seats**, calculated from
the resolution of `availabilityRatio`:

```text
1 seat = 1 / 385 ≈ 0.0026
```

## Attribute notes

- IMAX screenings in the Czech tenant do **not** include the `imax` attribute.
  Although it exists in the attribute catalogue, it does not appear on events.
  The watcher identifies relevant screenings using `70-mm` and
  `auditorium = IMAX VOLVO`.
- Film-level `attributeIds` are aggregated across all screenings in the entire
  cinema network. Only event-level attributes are suitable for filtering.
- `businessDay` is not always equal to the calendar date. For example, a
  screening at 00:20 belongs to the previous business day.

## Limitations

- **Seat map and specific rows:** The booking system is protected by aggressive
  Cloudflare bot protection, so the watcher does not automate seat-map access.
  The `availabilityRatio` delta and direct booking link are sufficient for the
  current workflow: open the email link to inspect the seat map in a browser.
  Row-level filtering may be added later.
- **Responsible API usage:** The watcher uses delays between requests and an
  honest `User-Agent`. Each scan performs one request for matching dates and
  one additional request for each date returned by the API.

## Quick start

The local runner requires only Python 3.11 or newer:

```bash
cd src
python local_run.py --once          # Run once and initialize state.json
python local_run.py --interval 60   # Poll every 60 seconds and print alerts
```

This README file will be completely rewritten in future. For now an important thing is that terraform will require an existing SES email identity to import during `terraform plan`.

## Configuration

Configuration is provided through environment variables:

| Variable                   | Default                           | Description                                                                             |
| -------------------------- | --------------------------------- | --------------------------------------------------------------------------------------- |
| `CINEMA_ID`                | `1052`                            | Cinema ID; defaults to Praha Flora                                                      |
| `FILM_ID`                  | —                                 | Exact film ID, for example `7268s2r`; takes precedence over `FILM_MATCH`                |
| `FILM_MATCH`               | `odys`                            | Case-insensitive fragment of the film title                                             |
| `REQUIRED_ATTRS`           | `70-mm`                           | Required event attributes as CSV; leave empty to accept all screenings                  |
| `HORIZON_DAYS`             | `45`                              | Number of days to scan ahead                                                            |
| `MIN_RATIO_DELTA`          | `0.002`                           | Minimum increase in available seats; one seat is approximately `0.0026`                 |
| `CAPACITY`                 | `385`                             | Auditorium capacity used to display seat counts; set to `0` to display percentages      |
| `ALERT_COOLDOWN_MIN`       | `15`                              | Cooldown in minutes per screening and alert type                                        |
| `INTENSIVE`                | `false`                           | For AWS Lambda, poll repeatedly until the timeout; intended for Tuesday ticket releases |
| `INTENSIVE_INTERVAL_S`     | `15`                              | Delay between scans in intensive mode                                                   |
| `STATE_BACKEND`            | `file`                            | State backend: `file` or `dynamodb`                                                     |
| `STATE_FILE` / `DDB_TABLE` | `state.json` / `cc-watcher-state` | File path or DynamoDB table used to store state                                         |
| `NOTIFY_BACKEND`           | `console`                         | Notification backend: `console` or `ses`                                                |
| `SES_FROM` / `SES_TO`      | —                                 | SES sender and comma-separated recipients                                               |
| `WATCHER_AWS_REGION`       | `eu-central-1`                    | AWS region                                                                              |
