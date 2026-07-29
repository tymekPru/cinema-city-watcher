# cc-watcher — ticket watcher for Cinema City (CZ)

Cinema City showtime watcher (start: czech version, Praha Flora IMAX)
Checks for available spots for movies and sends an email notification

## Configuration

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `CINEMA_ID` | `1052` | kino (Praha Flora) |
| `FILM_ID` | – | dokładne id filmu (np. `7268s2r`); ma pierwszeństwo |
| `FILM_MATCH` | `odys` | fragment nazwy filmu |
| `REQUIRED_ATTRS` | `70-mm` | wymagane atrybuty seansu (CSV); puste = wszystkie |
| `HORIZON_DAYS` | `45` | ile dni do przodu skanować |
| `MIN_RATIO_DELTA` | `0.002` | próg przyrostu wolnych miejsc (1 miejsce = 0.0026) |
| `CAPACITY` | `385` | pojemność sali (IMAX VOLVO) — alerty pokażą liczbę miejsc; `0` = pokaż % |
| `ALERT_COOLDOWN_MIN` | `15` | cisza po alercie danego typu dla seansu |
| `INTENSIVE` | `false` | Lambda: pętla wewnętrzna do końca timeoutu (środy) |
| `INTENSIVE_INTERVAL_S` | `15` | odstęp przebiegów w trybie intensywnym |
| `STATE_BACKEND` | `file` | `file` \| `dynamodb` |
| `STATE_FILE` / `DDB_TABLE` | `state.json` / `cc-watcher-state` | magazyn stanu |
| `NOTIFY_BACKEND` | `console` | `console` \| `ses` |
| `SES_FROM` / `SES_TO` | – | nadawca / odbiorcy (CSV) dla SES |
| `WATCHER_AWS_REGION` | `eu-central-1` | region AWS |