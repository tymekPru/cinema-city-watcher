# cc-watcher — ticket watcher for Cinema City (CZ)

Cinema City showtime watcher (start: czech version, Praha Flora IMAX)
Checks for available spots for movies and sends an email notification

<<<<<<< HEAD
## Configuration
=======
## Jak to działa (ustalenia o API — 2026-07-29)

Cinema City ma nieoficjalne, publiczne JSON API repertuaru (to samo, z którego
korzysta ich strona). Baza dla Czech (tenant `10101`):

```
https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/
```

Kluczowe endpointy (wszystkie zwykłe GET, bez autoryzacji):

| Endpoint | Co daje |
|---|---|
| `cinemas/with-event/until/{YYYY-MM-DD}?attr=&lang=cs_CZ` | lista kin (Praha Flora = `1052`) |
| `films/until/{YYYY-MM-DD}?attr=&lang=cs_CZ` | lista filmów (Odyssea = `7268s2r`) |
| `film-events/in-cinema/{cinemaId}/at-date/{YYYY-MM-DD}?attr=&lang=cs_CZ` | filmy + seanse danego dnia |
| `dates/in-cinema/{cinemaId}/until/{YYYY-MM-DD}?attr=70-mm&lang=cs_CZ` | dni, w których są pasujące seanse — jednym requestem |
| `attributes?lang=cs_CZ` | katalog wszystkich atrybutów (słownik `attributeIds`) |

Filtr `attr=` działa **po stronie serwera**, ale wiele wartości łączy się jak **OR**
(nie AND) — dlatego serwerowo wysyłamy jeden atrybut (zawężenie), a resztę
dociskamy u siebie. `dates/...` + `attr=70-mm` zbija przebieg z ~46 requestów do ~6.

## Do wyklikania w Postmanie

Trzy zapytania, od których warto zacząć (zwykły GET, bez nagłówków, bez auth):

```
GET https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/dates/in-cinema/1052/until/2026-09-30?attr=70-mm&lang=cs_CZ
GET https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/film-events/in-cinema/1052/at-date/2026-08-01?attr=70-mm&lang=cs_CZ
GET https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/attributes?lang=cs_CZ
```

W drugim szukaj w `body.events[]` pól `soldOut`, `availabilityRatio`, `auditorium`
i `bookingRouterLaunchLink` — na tych czterech stoi cały watcher.

Obiekt seansu (event) zawiera **wszystko, czego potrzebujemy**:

- `soldOut` (bool) i `availabilityRatio` (ułamek wolnych miejsc, rozdzielczość ~1 miejsca),
- `attributeIds` — m.in. `70-mm` (seanse 70mm w sali „IMAX VOLVO"),
- `bookingRouterLaunchLink` — działający deep link do zakupu:
  `https://www.cinemacity.cz/cz/booking-router/launch/{eventId}?lang=cs`.

Uwaga: pole `bookingLink` (`tickets.cinemacity.cz/api/order/...`) jest **martwe**
(w `compositeBookingLink` figuruje jako `obsoleteBookingUrl` i zwraca 404).
Właściwy system rezerwacji to `tickets.rel.cinemacity.cz`.

### Detekcja (trzy sygnały)

1. **NOWY SEANS** — pojawił się pasujący seans, którego nie było (środowe dropy nowych terminów).
2. **POWRÓT BILETÓW** — seans przeszedł z `soldOut=true` na `false`.
3. **NOWE MIEJSCA** — `availabilityRatio` wzrósł o próg (domyślnie ~1 miejsce).
   Liczymy **przyrost względem ostatniego stanu**, więc miejsca wiszące wolne od zawsze
   (np. dla wózków) nie robią fałszywych alarmów — alarmuje dopiero zmiana.

Pierwszy przebieg tylko inicjalizuje stan (bez lawiny alertów). Wszystkie alerty
z jednego przebiegu idą w jednym mailu. Cooldown na parę (seans, typ alertu).

### Kiedy wpadają bilety (ustalenia z researchu)

**We wtorki przed południem** — nie w środy. Czeskie kina programują „tydzień kinowy"
czwartek → środa, a sprzedaż na kolejny tydzień otwiera się w poprzedzający wtorek rano
(Forbes.cz, kinomaniak.cz). Środa to ostatni dzień tygodnia kinowego, stąd wrażenie,
że „już nic nie ma". Dokładna godzina nie jest nigdzie publikowana (tylko „dopoledne"),
więc tryb intensywny warto trzymać od ~6:30. Horyzont sprzedaży to zwykle ~1 tydzień.

Kontekst: Flora to jedno z 3 kin w UE z prawdziwą projekcją 15/70mm (obok Brukseli
i Montpellier). Seanse 70mm schodzą w godziny, pojemność sali IMAX VOLVO = **385 miejsc**
(wyliczone z rozdzielczości `availabilityRatio`: 1 miejsce = 1/385 ≈ 0.0026).

### Uwagi o atrybutach

- Seanse IMAX w czeskim tenantcie **nie mają** atrybutu `imax` (jest w słowniku, ale nie
  występuje na żadnym evencie) — rozpoznajemy je po `70-mm` oraz `auditorium` = `IMAX VOLVO`.
- `attributeIds` na poziomie **filmu** są zagregowane po wszystkich seansach w całej sieci —
  do filtrowania nadają się tylko te na poziomie **eventu**.
- `businessDay` ≠ data kalendarzowa: seans o 00:20 należy do dnia poprzedniego.

### Ograniczenia

- **Mapa sali (konkretne rzędy / miejsca dla wózków)**: system rezerwacji siedzi za
  agresywnym Cloudflare bot-protection — nie automatyzujemy tego (blokady + ToS).
  W praktyce wystarcza delta `availabilityRatio` + deep link: klikasz z maila
  i w 5 sekund widzisz mapę sali w przeglądarce. Filtr rzędów = ewentualny etap 2.
- API repertuaru traktujemy grzecznie: przerwy między requestami, uczciwy User-Agent,
  jeden przebieg = `HORIZON_DAYS + 1` requestów.

## Szybki start (lokalnie, zero zależności — czysty Python 3.11+)

```bash
cd src
python local_run.py --once          # jeden przebieg (inicjalizuje state.json)
python local_run.py --interval 60   # pętla co 60 s, alerty na konsolę
```

## Konfiguracja (zmienne środowiskowe)
>>>>>>> 28194c2 (download optimalization)

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