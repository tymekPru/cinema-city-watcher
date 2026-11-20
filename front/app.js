"use strict";

// ---------- translations ----------

const I18N = {
  en: {
    "title": "Cinema City watcher",
    "tagline": "Alerts for new screenings and freed seats",
    "lang.pl": "Polski",
    "lang.en": "English",
    "settings": "Settings",
    "addAlert": "Add alert",
    "close": "Close",
    "th.film": "Film",
    "th.cinema": "Cinema",
    "th.format": "Format",
    "th.language": "Language",
    "th.dates": "Dates",
    "th.status": "Status",
    "th.lastCheck": "Last check",
    "th.tracked": "Tracked",
    "empty": "No alerts yet. Add one to start watching.",
    "loadError": "Could not load alerts: {msg}",
    "serverError": "Could not reach the server: {msg}",
    "status.active": "Active",
    "status.upcoming": "Upcoming",
    "status.expired": "Expired",
    "status.waiting": "Waiting",
    "status.waiting.title": "Tickets are not on sale yet",
    "any": "any",
    "anyDates": "any dates",
    "fromDate": "from {d}",
    "untilDate": "until {d}",
    "seatsTag": "seats",
    "comingSoon": "Coming soon",
    "alerted": "alerted {t}",
    "never": "never",
    "justNow": "just now",
    "minAgo": "{n} min ago",
    "hAgo": "{n} h ago",
    "dAgo": "{n} d ago",
    "delete": "Delete",
    "confirmDelete": "Delete the alert for “{film}” at {cinema}?",
    "deleteFailed": "Delete failed: {msg}",
    "d.alert": "Alert",
    "d.country": "Country",
    "d.film": "Film",
    "d.cinema": "Cinema",
    "d.format": "Format",
    "d.language": "Language",
    "d.dates": "Dates",
    "d.seats": "Seat changes",
    "d.created": "Created",
    "d.lastCheck": "Last check",
    "d.id": "Id",
    "d.tracked": "Tracked screenings ({n})",
    "yes": "yes",
    "no": "no",
    "loading": "Loading…",
    "noScreenings": "No matching screenings on sale right now.",
    "notChecked": "Not checked yet. Run the watcher once.",
    "waitingSoon": "Tickets are not on sale yet. The watcher is waiting for presale to open.",
    "soldOut": "sold out",
    "pctSold": "{n}% sold",
    "book": "Book",
    "newAlert": "New alert",
    "back": "Back",
    "next": "Next",
    "saveAlert": "Save alert",
    "step.country": "Country",
    "step.movie": "Movie",
    "step.cinema": "Cinema",
    "step.format": "Format",
    "step.language": "Language",
    "step.dates": "Dates & options",
    "country.cz": "Czechia",
    "country.pl": "Poland",
    "country.q": "Which country?",
    "country.hint": "Film catalogues differ per country, so this comes first.",
    "movie.q": "Which movie?",
    "movie.hint": "{n} films on sale, {m} announced.",
    "movie.search": "Search films…",
    "movie.soonOnly": "Coming soon only",
    "movie.release": "release {d}",
    "movie.min": "{n} min",
    "movie.noMatch": "No films match.",
    "cinema.q": "Which cinema?",
    "cinema.hint": "{n} cinemas, {m} with an IMAX screen.",
    "cinema.search": "Search cinemas…",
    "cinema.imaxOnly": "IMAX only",
    "cinema.noMatch": "No cinemas match.",
    "format.q": "Which format?",
    "format.hint": "One format per alert. Formats this cinema does not have, or this film is not offered in, are greyed out.",
    "format.hintSoon": "One format per alert. Which formats this film will get is not known before presale, so only formats this cinema does not have are greyed out.",
    "format.any": "Any format",
    "format.anyMeta": "Alert on every screening of this film",
    "format.notAtCinema": "not available at this cinema",
    "format.notForFilm": "not offered for this film",
    "language.q": "Which language version?",
    "language.hint": "Based on what this film is offered in.",
    "language.hintNone": "No language details for this film.",
    "language.any": "Any language",
    "language.subbed": "Subtitled",
    "language.dubbed": "Dubbed",
    "language.original": "Original",
    "language.subMeta": "original {o}, subtitles {s}",
    "language.subMetaNoAudio": "subtitles {s}",
    "dates.q": "Dates and options",
    "dates.hint": "Leave the dates empty to watch every screening, whenever it is scheduled. New screenings are always reported.",
    "dates.from": "From",
    "dates.to": "To",
    "dates.clear": "Clear",
    "seats.label": "Also notify when seats free up on existing screenings",
    "seats.help": "For a sold-out screening on the date you want. Ignored for screenings that appear later, which are reported anyway.",
    "err.order": "The start date must not be after the end date.",
    "err.duplicate": "An identical alert already exists: {film} at {cinema}.",
    "err.no_topic": "No ntfy topic configured. Save one first.",
    "err.upstream": "The Cinema City API did not answer: {detail}",
    "err.notify_failed": "Sending failed: {detail}",
    "st.hint": "Saved to appsettings.json. A running watcher picks changes up on its next sweep. Notifications go to the console and, when a topic is set, to ntfy.",
    "st.save": "Save",
    "st.saveTest": "Save & send test",
    "st.testSent": "Test sent to topic “{topic}”.",
    "st.mustBeNumber": "{label} must be a number.",
    "st.server": "ntfy server",
    "st.server.help": "Public ntfy.sh or your own instance.",
    "st.topic": "ntfy topic",
    "st.topic.help": "Pick a unique, hard-to-guess name and subscribe to it in the ntfy app. Empty disables ntfy.",
    "st.token": "ntfy access token",
    "st.token.help": "Only needed for protected topics.",
    "st.priority": "Notification priority",
    "st.priority.help": "ntfy priority; high and urgent also make the phone vibrate or ring.",
    "st.gap": "Request gap (seconds)",
    "st.gap.help": "Minimum pause between two requests to the Cinema City API.",
    "st.cache": "Catalogue cache (seconds)",
    "st.cache.help": "How long film, cinema and format lists are cached for this UI.",
    "st.delta": "Minimum seat change (ratio)",
    "st.delta.help": "Rise in the free-seat ratio that counts as freed seats. One seat in a 385-seat hall is about 0.0026.",
    "st.cooldown": "Alert cooldown (minutes)",
    "st.cooldown.help": "Do not repeat the same alert for the same screening within this time.",
    "st.poll": "Poll interval (seconds)",
    "st.poll.help": "Pause between sweeps when the watcher runs with --keep-alive.",
    "st.dataDir": "Data directory",
    "st.dataDir.help": "Where alerts.json and state.json live. Relative to appsettings.json.",
  },
  pl: {
    "title": "Cinema City watcher",
    "tagline": "Powiadomienia o nowych seansach i zwolnionych miejscach",
    "lang.pl": "Polski",
    "lang.en": "English",
    "settings": "Ustawienia",
    "addAlert": "Dodaj alert",
    "close": "Zamknij",
    "th.film": "Film",
    "th.cinema": "Kino",
    "th.format": "Format",
    "th.language": "Język",
    "th.dates": "Daty",
    "th.status": "Status",
    "th.lastCheck": "Sprawdzono",
    "th.tracked": "Śledzone",
    "empty": "Nie masz jeszcze alertów. Dodaj pierwszy, aby zacząć obserwować.",
    "loadError": "Nie udało się wczytać alertów: {msg}",
    "serverError": "Brak połączenia z serwerem: {msg}",
    "status.active": "Aktywny",
    "status.upcoming": "Nadchodzący",
    "status.expired": "Zakończony",
    "status.waiting": "Czeka",
    "status.waiting.title": "Bilety nie są jeszcze w sprzedaży",
    "any": "dowolny",
    "anyDates": "dowolne daty",
    "fromDate": "od {d}",
    "untilDate": "do {d}",
    "seatsTag": "miejsca",
    "comingSoon": "Wkrótce",
    "alerted": "powiadomienie {t}",
    "never": "nigdy",
    "justNow": "przed chwilą",
    "minAgo": "{n} min temu",
    "hAgo": "{n} godz. temu",
    "dAgo": "{n} dni temu",
    "delete": "Usuń",
    "confirmDelete": "Usunąć alert dla „{film}” w kinie {cinema}?",
    "deleteFailed": "Nie udało się usunąć: {msg}",
    "d.alert": "Alert",
    "d.country": "Kraj",
    "d.film": "Film",
    "d.cinema": "Kino",
    "d.format": "Format",
    "d.language": "Język",
    "d.dates": "Daty",
    "d.seats": "Zwolnione miejsca",
    "d.created": "Utworzono",
    "d.lastCheck": "Ostatnie sprawdzenie",
    "d.id": "Id",
    "d.tracked": "Śledzone seanse ({n})",
    "yes": "tak",
    "no": "nie",
    "loading": "Wczytywanie…",
    "noScreenings": "Obecnie brak pasujących seanów w sprzedaży.",
    "notChecked": "Jeszcze nie sprawdzono. Uruchom watcher.",
    "waitingSoon": "Bilety nie są jeszcze w sprzedaży. Watcher czeka na start przedsprzedaży.",
    "soldOut": "wyprzedane",
    "pctSold": "{n}% sprzedane",
    "book": "Kup",
    "newAlert": "Nowy alert",
    "back": "Wstecz",
    "next": "Dalej",
    "saveAlert": "Zapisz alert",
    "step.country": "Kraj",
    "step.movie": "Film",
    "step.cinema": "Kino",
    "step.format": "Format",
    "step.language": "Język",
    "step.dates": "Daty i opcje",
    "country.cz": "Czechy",
    "country.pl": "Polska",
    "country.q": "Który kraj?",
    "country.hint": "Repertuar różni się w każdym kraju, dlatego zaczynamy od tego.",
    "movie.q": "Który film?",
    "movie.hint": "{n} filmów w sprzedaży, {m} zapowiedzi.",
    "movie.search": "Szukaj filmu…",
    "movie.soonOnly": "Tylko zapowiedzi",
    "movie.release": "premiera {d}",
    "movie.min": "{n} min",
    "movie.noMatch": "Brak pasujących filmów.",
    "cinema.q": "Które kino?",
    "cinema.hint": "{n} kin, {m} z salą IMAX.",
    "cinema.search": "Szukaj kina…",
    "cinema.imaxOnly": "Tylko IMAX",
    "cinema.noMatch": "Brak pasujących kin.",
    "format.q": "Który format?",
    "format.hint": "Jeden format na alert. Formaty, których nie ma w tym kinie lub w których nie jest grany ten film, są wyszarzone.",
    "format.hintSoon": "Jeden format na alert. Przed przedsprzedażą nie wiadomo, w jakich formatach będzie grany ten film, więc wyszarzone są tylko formaty, których nie ma w tym kinie.",
    "format.any": "Dowolny format",
    "format.anyMeta": "Powiadamiaj o każdym seansie tego filmu",
    "format.notAtCinema": "niedostępny w tym kinie",
    "format.notForFilm": "ten film nie jest grany w tym formacie",
    "language.q": "Która wersja językowa?",
    "language.hint": "Na podstawie wersji, w których grany jest ten film.",
    "language.hintNone": "Brak informacji o wersjach językowych tego filmu.",
    "language.any": "Dowolna wersja",
    "language.subbed": "Z napisami",
    "language.dubbed": "Dubbing",
    "language.original": "Oryginalna",
    "language.subMeta": "oryginał {o}, napisy {s}",
    "language.subMetaNoAudio": "napisy {s}",
    "dates.q": "Daty i opcje",
    "dates.hint": "Zostaw daty puste, aby obserwować każdy seans niezależnie od terminu. Nowe seanse są zgłaszane zawsze.",
    "dates.from": "Od",
    "dates.to": "Do",
    "dates.clear": "Wyczyść",
    "seats.label": "Powiadamiaj też, gdy zwolnią się miejsca na istniejących seansach",
    "seats.help": "Dla wyprzedanego seansu w wybranym dniu. Seanse dodane później są zgłaszane niezależnie od tej opcji.",
    "err.order": "Data początkowa nie może być późniejsza niż końcowa.",
    "err.duplicate": "Taki alert już istnieje: {film} w kinie {cinema}.",
    "err.no_topic": "Nie ustawiono tematu ntfy. Najpierw zapisz temat.",
    "err.upstream": "API Cinema City nie odpowiedziało: {detail}",
    "err.notify_failed": "Wysyłka nie powiodła się: {detail}",
    "st.hint": "Zapisywane do appsettings.json. Działający watcher wczyta zmiany przy kolejnym sprawdzeniu. Powiadomienia trafiają do konsoli oraz, po ustawieniu tematu, do ntfy.",
    "st.save": "Zapisz",
    "st.saveTest": "Zapisz i wyślij test",
    "st.testSent": "Test wysłany do tematu „{topic}”.",
    "st.mustBeNumber": "{label} musi być liczbą.",
    "st.server": "Serwer ntfy",
    "st.server.help": "Publiczny ntfy.sh albo własna instancja.",
    "st.topic": "Temat ntfy",
    "st.topic.help": "Wybierz unikalną, trudną do odgadnięcia nazwę i zasubskrybuj ją w aplikacji ntfy. Puste pole wyłącza ntfy.",
    "st.token": "Token dostępu ntfy",
    "st.token.help": "Potrzebny tylko dla chronionych tematów.",
    "st.priority": "Priorytet powiadomień",
    "st.priority.help": "Priorytet ntfy; high i urgent dodatkowo wibrują lub dzwonią.",
    "st.gap": "Odstęp między zapytaniami (s)",
    "st.gap.help": "Minimalna pauza między dwoma zapytaniami do API Cinema City.",
    "st.cache": "Pamięć podręczna katalogu (s)",
    "st.cache.help": "Jak długo listy filmów, kin i formatów są trzymane w pamięci na potrzeby tego UI.",
    "st.delta": "Minimalna zmiana miejsc (ułamek)",
    "st.delta.help": "Wzrost udziału wolnych miejsc uznawany za zwolnione miejsca. Jedno miejsce w sali na 385 osób to ok. 0,0026.",
    "st.cooldown": "Przerwa między alertami (min)",
    "st.cooldown.help": "Nie powtarzaj tego samego alertu dla tego samego seansu w tym czasie.",
    "st.poll": "Częstotliwość sprawdzania (s)",
    "st.poll.help": "Pauza między sprawdzeniami, gdy watcher działa z --keep-alive.",
    "st.dataDir": "Katalog danych",
    "st.dataDir.help": "Gdzie leżą alerts.json i state.json. Względem appsettings.json.",
  },
};
const LOCALES = { en: "en-GB", pl: "pl-PL" };

function detectLang() {
  try {
    const saved = localStorage.getItem("lang");
    if (saved in I18N) return saved;
  } catch (_) {
    /* storage unavailable */
  }
  return (navigator.language || "").toLowerCase().startsWith("pl") ? "pl" : "en";
}

let lang = detectLang();

function t(key, params) {
  let text = I18N[lang][key] ?? I18N.en[key] ?? key;
  if (params) for (const [k, v] of Object.entries(params)) text = text.split(`{${k}}`).join(String(v ?? ""));
  return text;
}

function applyStatic() {
  document.documentElement.lang = lang;
  document.title = t("title");
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  for (const node of document.querySelectorAll("[data-i18n-aria]")) node.setAttribute("aria-label", t(node.dataset.i18nAria));
  for (const b of document.querySelectorAll(".lang button")) b.classList.toggle("active", b.dataset.lang === lang);
}

function setLang(code) {
  if (!(code in I18N) || code === lang) return;
  lang = code;
  try {
    localStorage.setItem("lang", code);
  } catch (_) {
    /* storage unavailable */
  }
  applyStatic();
  loadAlerts();
  if (!$("wizard").hidden) wz.render();
  if (!$("settings").hidden) settings.open();
}

// ---------- helpers ----------

const STEP_KEYS = ["country", "movie", "cinema", "format", "language", "dates"];
const LANGUAGE_KEYS = { subbed: "language.subbed", dubbed: "language.dubbed", original: "language.original" };
const NTFY_PRIORITIES = ["min", "low", "default", "high", "urgent"];
const SETTINGS_FIELDS = [
  { path: "notify.ntfy.server", key: "st.server", type: "text" },
  { path: "notify.ntfy.topic", key: "st.topic", type: "text" },
  { path: "notify.ntfy.token", key: "st.token", type: "password" },
  { path: "notify.ntfy.priority", key: "st.priority", type: "select", options: NTFY_PRIORITIES },
  { path: "api.requestGapSeconds", key: "st.gap", step: "0.05" },
  { path: "api.cacheSeconds", key: "st.cache", step: "1" },
  { path: "alerts.minRatioDelta", key: "st.delta", step: "0.001" },
  { path: "alerts.cooldownMinutes", key: "st.cooldown", step: "1" },
  { path: "runtime.pollIntervalSeconds", key: "st.poll", step: "1" },
  { path: "runtime.dataDir", key: "st.dataDir", type: "text" },
];
const getPath = (obj, path) => path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);
const setPath = (obj, path, value) => {
  const keys = path.split(".");
  const last = keys.pop();
  keys.reduce((o, k) => (o[k] ||= {}), obj)[last] = value;
};
const fieldId = (f) => "st-" + f.path.replace(/\./g, "-");

const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined && v !== false) node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children) if (c !== null && c !== undefined && c !== "") node.append(c instanceof Node ? c : document.createTextNode(c));
  return node;
};

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || `${res.status} ${res.statusText}`);
    err.code = data.code;
    err.data = data;
    throw err;
  }
  return data;
}

// Server errors carry a code; known ones are shown in the page language.
function errText(e) {
  if (e.code && I18N.en["err." + e.code]) return t("err." + e.code, e.data);
  return e.message;
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  return d.toLocaleDateString(LOCALES[lang], { day: "numeric", month: "short", year: "numeric" });
}

function fmtDateTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString(LOCALES[lang], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function relTime(iso) {
  if (!iso) return t("never");
  const s = Math.round((Date.now() - new Date(iso)) / 1000);
  if (s < 60) return t("justNow");
  if (s < 3600) return t("minAgo", { n: Math.floor(s / 60) });
  if (s < 86400) return t("hAgo", { n: Math.floor(s / 3600) });
  return t("dAgo", { n: Math.floor(s / 86400) });
}

function dateRange(a) {
  if (a.dateFrom && a.dateTo) return `${fmtDate(a.dateFrom)} – ${fmtDate(a.dateTo)}`;
  if (a.dateFrom) return t("fromDate", { d: fmtDate(a.dateFrom) });
  if (a.dateTo) return t("untilDate", { d: fmtDate(a.dateTo) });
  return t("anyDates");
}

// ---------- overview table ----------

const formatLabels = {};
let countries = [];
const expanded = new Set();

function splitAttrs(attrs) {
  return {
    format: attrs.find((a) => !(a in LANGUAGE_KEYS)),
    language: attrs.find((a) => a in LANGUAGE_KEYS),
  };
}

const countryName = (code) => (I18N.en["country." + code] ? t("country." + code) : (countries.find((c) => c.code === code) || {}).name || code.toUpperCase());
const formatLabel = (id) => (id ? formatLabels[id] || id : t("any"));
const languageLabel = (id) => (id ? (LANGUAGE_KEYS[id] ? t(LANGUAGE_KEYS[id]) : id) : t("any"));
const anyOr = (value) => (value ? value : el("span", { class: "muted" }, t("any")));
const tag = (text) => el("span", { class: "tag", style: "margin-left:8px" }, text);

function row(a) {
  const { format, language } = splitAttrs(a.attrs);
  return el(
    "tr",
    { class: "row" + (expanded.has(a.id) ? " open" : ""), onclick: () => toggleDetails(a) },
    el("td", { class: "wrap" }, a.film.name, a.onSale ? "" : tag(t("comingSoon")), el("span", { class: "sub" }, countryName(a.country))),
    el("td", { class: "wrap" }, a.cinema.name, a.cinema.imax ? tag("IMAX") : ""),
    el("td", {}, anyOr(format && formatLabel(format))),
    el("td", {}, anyOr(language && languageLabel(language))),
    el("td", {}, dateRange(a), a.seatChanges ? tag(t("seatsTag")) : ""),
    el("td", {}, el("span", { class: `pill ${a.status}`, title: a.status === "waiting" ? t("status.waiting.title") : null }, t("status." + a.status))),
    el("td", {}, relTime(a.lastSweep), a.lastAlert ? el("span", { class: "sub" }, t("alerted", { t: relTime(a.lastAlert) })) : ""),
    el("td", { class: "num" }, String(a.tracked)),
    el(
      "td",
      { class: "actions" },
      el("button", { class: "btn danger", onclick: (e) => { e.stopPropagation(); removeAlert(a); } }, t("delete"))
    )
  );
}

function fillClass(fill, soldOut) {
  if (soldOut || fill >= 0.9) return "hot";
  if (fill >= 0.6) return "warm";
  return "cool";
}

function detailsRow(a) {
  const { format, language } = splitAttrs(a.attrs);
  const props = el(
    "dl",
    { class: "props" },
    el("dt", {}, t("d.country")), el("dd", {}, countryName(a.country)),
    el("dt", {}, t("d.film")), el("dd", {}, a.film.name, el("span", { class: "sub" }, a.film.id + (a.film.releaseDate ? ` · ${t("movie.release", { d: fmtDate(a.film.releaseDate) })}` : ""))),
    el("dt", {}, t("d.cinema")), el("dd", {}, a.cinema.name + (a.cinema.imax ? " (IMAX)" : ""), el("span", { class: "sub" }, a.cinema.id)),
    el("dt", {}, t("d.format")), el("dd", {}, formatLabel(format)),
    el("dt", {}, t("d.language")), el("dd", {}, languageLabel(language)),
    el("dt", {}, t("d.dates")), el("dd", {}, dateRange(a)),
    el("dt", {}, t("d.seats")), el("dd", {}, t(a.seatChanges ? "yes" : "no")),
    el("dt", {}, t("d.created")), el("dd", {}, fmtDateTime(a.createdAt)),
    el("dt", {}, t("d.lastCheck")), el("dd", {}, relTime(a.lastSweep)),
    el("dt", {}, t("d.id")), el("dd", {}, a.id)
  );
  const shots = el("div", { class: "shots" }, el("p", { class: "muted" }, t("loading")));
  api(`/api/alerts/${a.id}/events`)
    .then((events) => {
      if (!events.length) {
        const msg = a.status === "waiting" ? "waitingSoon" : a.lastSweep ? "noScreenings" : "notChecked";
        shots.replaceChildren(el("p", { class: "muted" }, t(msg)));
        return;
      }
      shots.replaceChildren(
        ...events.map((ev) => {
          const fill = Math.min(1, Math.max(0, 1 - (ev.free || 0)));
          return el(
            "div",
            { class: "shot" + (ev.soldOut ? " soldout" : "") },
            el("span", { class: "when" }, fmtDateTime(ev.when)),
            el("span", { class: "room", title: ev.room || "" }, ev.room || ""),
            el("div", { class: "bar" }, el("div", { class: `fill ${fillClass(fill, ev.soldOut)}`, style: `width:${Math.round(fill * 100)}%` })),
            el("span", { class: "pct" }, ev.soldOut ? t("soldOut") : t("pctSold", { n: Math.round(fill * 100) })),
            ev.book ? el("a", { href: ev.book, target: "_blank", rel: "noopener" }, t("book")) : ""
          );
        })
      );
    })
    .catch((e) => shots.replaceChildren(el("p", { class: "error" }, errText(e))));
  return el(
    "tr",
    { class: "details" },
    el(
      "td",
      { colspan: "9" },
      el(
        "div",
        { class: "detail-grid" },
        el("div", {}, el("h4", {}, t("d.alert")), props),
        el("div", {}, el("h4", {}, t("d.tracked", { n: a.tracked })), shots)
      )
    )
  );
}

function toggleDetails(a) {
  if (expanded.has(a.id)) expanded.delete(a.id);
  else expanded.add(a.id);
  loadAlerts();
}

let lastAlerts = [];

async function loadAlerts() {
  const rows = $("rows");
  const err = $("load-error");
  err.hidden = true;
  try {
    lastAlerts = await api("/api/alerts");
    for (const id of expanded) if (!lastAlerts.some((a) => a.id === id)) expanded.delete(id);
    rows.replaceChildren(...lastAlerts.flatMap((a) => (expanded.has(a.id) ? [row(a), detailsRow(a)] : [row(a)])));
    $("empty").hidden = lastAlerts.length > 0;
    $("alerts").hidden = lastAlerts.length === 0;
  } catch (e) {
    err.textContent = t("loadError", { msg: errText(e) });
    err.hidden = false;
  }
}

async function removeAlert(a) {
  if (!confirm(t("confirmDelete", { film: a.film.name, cinema: a.cinema.name }))) return;
  try {
    await api(`/api/alerts/${a.id}`, { method: "DELETE" });
    await loadAlerts();
  } catch (e) {
    alert(t("deleteFailed", { msg: errText(e) }));
  }
}

async function loadFormatLabels() {
  // Labels are the same in every country; the first one that answers wins.
  for (const c of countries) {
    try {
      for (const f of await api(`/api/${c.code}/formats`)) formatLabels[f.id] = f.label;
      return;
    } catch (_) {
      /* try the next country */
    }
  }
}

// ---------- settings ----------

const settings = {
  open() {
    $("settings").hidden = false;
    this.showError("");
    $("st-fields").replaceChildren(el("p", { class: "muted" }, t("loading")));
    api("/api/settings")
      .then((data) => {
        $("st-fields").replaceChildren(
          ...SETTINGS_FIELDS.map((f) => {
            const value = getPath(data, f.path);
            const input =
              f.type === "select"
                ? el("select", { id: fieldId(f) }, ...f.options.map((o) => el("option", { value: o, selected: o === value }, o)))
                : el("input", { id: fieldId(f), type: f.type || "number", step: f.step, min: f.type ? null : "0", value: value ?? "" });
            return el("div", { class: "field" }, el("label", { for: fieldId(f) }, t(f.key)), input, el("span", { class: "help" }, t(f.key + ".help")));
          })
        );
      })
      .catch((e) => this.showError(errText(e)));
  },
  close() {
    $("settings").hidden = true;
  },
  showError(msg, ok = false) {
    $("st-error").textContent = msg || "";
    $("st-error").hidden = !msg;
    $("st-error").classList.toggle("ok", ok);
  },
  collect() {
    const patch = {};
    for (const f of SETTINGS_FIELDS) {
      const input = $(fieldId(f));
      if (!input) return null;
      const isNumber = !f.type;
      const value = isNumber ? Number(input.value) : input.value;
      if (isNumber && !Number.isFinite(value)) {
        this.showError(t("st.mustBeNumber", { label: t(f.key) }));
        return null;
      }
      setPath(patch, f.path, value);
    }
    return patch;
  },
  async save(andTest = false) {
    this.showError("");
    const patch = this.collect();
    if (!patch) return;
    $("st-save").disabled = $("st-test").disabled = true;
    try {
      await api("/api/settings", { method: "PUT", body: JSON.stringify(patch) });
      if (andTest) {
        const res = await api("/api/notify/test", { method: "POST" });
        this.showError(t("st.testSent", { topic: res.topic }), true);
        return;
      }
      this.close();
    } catch (e) {
      this.showError(errText(e));
    } finally {
      $("st-save").disabled = $("st-test").disabled = false;
    }
  },
};

// ---------- wizard ----------

const wz = {
  step: 0,
  draft: {},
  cache: {},
  open() {
    this.step = 0;
    this.draft = { dateFrom: null, dateTo: null, seatChanges: false };
    this.cache = {};
    $("wizard").hidden = false;
    this.render();
  },
  close() {
    $("wizard").hidden = true;
  },
  showError(msg) {
    $("wz-error").textContent = msg || "";
    $("wz-error").hidden = !msg;
  },
  canAdvance() {
    const d = this.draft;
    return Boolean([d.country, d.film, d.cinema, "format" in d, "language" in d, true][this.step]);
  },
  async next() {
    this.showError("");
    if (this.step === STEP_KEYS.length - 1) return this.save();
    if (!this.canAdvance()) return;
    this.step += 1;
    this.render();
  },
  back() {
    this.showError("");
    if (this.step > 0) {
      this.step -= 1;
      this.render();
    }
  },
  pick(key, value) {
    this.draft[key] = value;
    // Choices downstream depend on this one.
    if (key === "country") {
      delete this.draft.film;
      delete this.draft.cinema;
    }
    if (key === "film" || key === "cinema") {
      delete this.draft.format;
      delete this.draft.language;
    }
    this.next();
  },
  fetch(path) {
    if (!this.cache[path]) this.cache[path] = api(path);
    return this.cache[path];
  },
  render() {
    $("steps").replaceChildren(
      ...STEP_KEYS.map((k, i) => el("li", { class: i < this.step ? "done" : i === this.step ? "current" : "" }, `${i + 1}. ${t("step." + k)}`))
    );
    $("wz-back").disabled = this.step === 0;
    $("wz-next").textContent = this.step === STEP_KEYS.length - 1 ? t("saveAlert") : t("next");
    $("wz-next").disabled = !this.canAdvance();
    const body = $("wz-body");
    body.replaceChildren(el("p", { class: "muted" }, t("loading")));
    this[STEP_KEYS[this.step]](body).catch((e) => body.replaceChildren(el("p", { class: "error" }, errText(e))));
  },

  choiceButton(it, selected, onPick) {
    return el(
      "button",
      { class: "choice" + (selected ? " selected" : ""), disabled: Boolean(it.disabled), onclick: () => onPick(it) },
      it.img ? el("img", { src: it.img, alt: "", loading: "lazy" }) : it.img === null ? el("div", { class: "img" }) : "",
      el("div", { class: "grow" }, el("div", { class: "title" }, it.title), it.meta ? el("div", { class: "meta" }, it.meta) : ""),
      it.badge ? el("span", { class: "badge" }, it.badge) : ""
    );
  },

  choices(body, title, hint, items, selected, onPick) {
    body.replaceChildren(
      el("h3", {}, title),
      el("p", { class: "hint muted" }, hint),
      el("div", { class: "choices" }, ...items.map((it) => this.choiceButton(it, selected === it.value, onPick)))
    );
  },

  switchControl(input, label) {
    return el("label", { class: "switch" }, input, el("span", { class: "track" }), label);
  },

  async country(body) {
    this.choices(
      body,
      t("country.q"),
      t("country.hint"),
      countries.map((c) => ({ value: c.code, title: countryName(c.code), meta: c.code.toUpperCase() })),
      this.draft.country,
      (it) => this.pick("country", it.value)
    );
  },

  async movie(body) {
    const films = await this.fetch(`/api/${this.draft.country}/films`);
    const search = el("input", { class: "search", type: "search", placeholder: t("movie.search") });
    const soonOnly = el("input", { type: "checkbox" });
    const list = el("div", { class: "choices" });
    const meta = (f) => {
      const parts = [f.releaseDate && t("movie.release", { d: fmtDate(f.releaseDate) })];
      if (!f.comingSoon) parts.push(f.length && t("movie.min", { n: f.length }), f.attributeIds.filter((a) => a in formatLabels).map(formatLabel).join(", "));
      return parts.filter(Boolean).join(" · ");
    };
    const draw = () => {
      const q = search.value.trim().toLowerCase();
      const shown = films.filter((f) => (!soonOnly.checked || f.comingSoon) && (!q || f.name.toLowerCase().includes(q)));
      list.replaceChildren(
        ...shown.map((f) =>
          this.choiceButton(
            { value: f.id, img: f.posterLink || null, title: f.name, meta: meta(f), badge: f.comingSoon ? t("comingSoon") : null, raw: f },
            this.draft.film && this.draft.film.id === f.id,
            (it) => this.pick("film", it.raw)
          )
        )
      );
      if (!shown.length) list.replaceChildren(el("p", { class: "muted" }, t("movie.noMatch")));
    };
    search.addEventListener("input", draw);
    soonOnly.addEventListener("change", draw);
    const soon = films.filter((f) => f.comingSoon).length;
    body.replaceChildren(
      el("h3", {}, t("movie.q")),
      el("p", { class: "hint muted" }, t("movie.hint", { n: films.length - soon, m: soon })),
      el("div", { class: "toolbar" }, search, this.switchControl(soonOnly, t("movie.soonOnly"))),
      list
    );
    draw();
    search.focus();
  },

  async cinema(body) {
    const cinemas = await this.fetch(`/api/${this.draft.country}/cinemas`);
    const search = el("input", { class: "search", type: "search", placeholder: t("cinema.search") });
    const imaxOnly = el("input", { type: "checkbox" });
    const list = el("div", { class: "choices" });
    const draw = () => {
      const q = search.value.trim().toLowerCase();
      const shown = cinemas.filter((c) => (!imaxOnly.checked || c.imax) && (!q || c.name.toLowerCase().includes(q)));
      list.replaceChildren(
        ...shown.map((c) =>
          this.choiceButton(
            { value: c.id, title: c.name, badge: c.imax ? "IMAX" : null, raw: c },
            this.draft.cinema && this.draft.cinema.id === c.id,
            (it) => this.pick("cinema", it.raw)
          )
        )
      );
      if (!shown.length) list.replaceChildren(el("p", { class: "muted" }, t("cinema.noMatch")));
    };
    search.addEventListener("input", draw);
    imaxOnly.addEventListener("change", draw);
    body.replaceChildren(
      el("h3", {}, t("cinema.q")),
      el("p", { class: "hint muted" }, t("cinema.hint", { n: cinemas.length, m: cinemas.filter((c) => c.imax).length })),
      el("div", { class: "toolbar" }, search, this.switchControl(imaxOnly, t("cinema.imaxOnly"))),
      list
    );
    draw();
    search.focus();
  },

  async format(body) {
    const formats = await this.fetch(`/api/${this.draft.country}/formats`);
    const film = this.draft.film;
    const onFilm = film.comingSoon ? null : new Set(film.attributeIds);
    const atCinema = new Set(this.draft.cinema.formats || []);
    const reason = (f) => (!atCinema.has(f.id) ? t("format.notAtCinema") : onFilm && !onFilm.has(f.id) ? t("format.notForFilm") : "");
    const items = [{ value: "", title: t("format.any"), meta: t("format.anyMeta") }].concat(
      formats
        .map((f) => ({ value: f.id, title: f.label, meta: reason(f), disabled: Boolean(reason(f)) }))
        .sort((a, b) => a.disabled - b.disabled)
    );
    this.choices(body, t("format.q"), t(film.comingSoon ? "format.hintSoon" : "format.hint"), items, this.draft.format, (it) => this.pick("format", it.value));
  },

  async language(body) {
    const langs = this.draft.film.languages || {};
    const original = (langs.original || []).join(", ");
    const subtitles = (langs.subtitles || []).join(", ");
    const items = [{ value: "", title: t("language.any"), meta: "" }];
    if (subtitles) items.push({ value: "subbed", title: t("language.subbed"), meta: original ? t("language.subMeta", { o: original, s: subtitles }) : t("language.subMetaNoAudio", { s: subtitles }) });
    if ((langs.dubbed || []).length) items.push({ value: "dubbed", title: t("language.dubbed"), meta: langs.dubbed.join(", ") });
    if (original && !subtitles) items.push({ value: "original", title: t("language.original"), meta: original });
    this.choices(body, t("language.q"), t(items.length > 1 ? "language.hint" : "language.hintNone"), items, this.draft.language, (it) => this.pick("language", it.value));
  },

  async dates(body) {
    const d = this.draft;
    const today = new Date().toISOString().slice(0, 10);
    const summary = el("div", { class: "summary" });
    const dateField = (key, label) => {
      const input = el("input", { type: "date", value: d[key] || "", min: today, oninput: () => { d[key] = input.value || null; drawSummary(); } });
      const clear = el("button", { class: "btn", type: "button", onclick: () => { input.value = ""; d[key] = null; drawSummary(); } }, t("dates.clear"));
      return el("div", { class: "field" }, el("label", {}, label), el("div", { class: "with-clear" }, input, clear));
    };
    const seats = el("input", { type: "checkbox", checked: d.seatChanges, onchange: () => { d.seatChanges = seats.checked; drawSummary(); } });
    const line = (label, value) => el("div", {}, el("span", {}, label), el("span", {}, value));
    const drawSummary = () =>
      summary.replaceChildren(
        line(t("d.film"), d.film.name),
        line(t("d.cinema"), d.cinema.name + (d.cinema.imax ? " (IMAX)" : "")),
        line(t("d.format"), formatLabel(d.format)),
        line(t("d.language"), languageLabel(d.language)),
        line(t("d.dates"), dateRange(d)),
        line(t("d.seats"), t(d.seatChanges ? "yes" : "no"))
      );
    body.replaceChildren(
      el("h3", {}, t("dates.q")),
      el("p", { class: "hint muted" }, t("dates.hint")),
      el("div", { class: "fields" }, dateField("dateFrom", t("dates.from")), dateField("dateTo", t("dates.to"))),
      el("label", { class: "check" }, seats, el("span", {}, el("span", { class: "title" }, t("seats.label")), el("span", { class: "help" }, t("seats.help")))),
      summary
    );
    drawSummary();
  },

  async save() {
    const d = this.draft;
    if (d.dateFrom && d.dateTo && d.dateFrom > d.dateTo) return this.showError(t("err.order"));
    const payload = {
      country: d.country,
      film: { id: d.film.id, name: d.film.name, releaseDate: d.film.releaseDate || null, comingSoon: Boolean(d.film.comingSoon) },
      cinema: { id: d.cinema.id, name: d.cinema.name, imax: d.cinema.imax },
      attrs: [d.format, d.language].filter(Boolean),
      dateFrom: d.dateFrom || null,
      dateTo: d.dateTo || null,
      seatChanges: Boolean(d.seatChanges),
    };
    $("wz-next").disabled = true;
    try {
      await api("/api/alerts", { method: "POST", body: JSON.stringify(payload) });
      this.close();
      await loadAlerts();
    } catch (e) {
      this.showError(errText(e));
      $("wz-next").disabled = false;
    }
  },
};

// ---------- boot ----------

$("add").addEventListener("click", () => wz.open());
$("wz-close").addEventListener("click", () => wz.close());
$("wz-back").addEventListener("click", () => wz.back());
$("wz-next").addEventListener("click", () => wz.next());
$("wizard").addEventListener("click", (e) => e.target === $("wizard") && wz.close());
$("settings-open").addEventListener("click", () => settings.open());
$("st-close").addEventListener("click", () => settings.close());
$("st-save").addEventListener("click", () => settings.save());
$("st-test").addEventListener("click", () => settings.save(true));
$("settings").addEventListener("click", (e) => e.target === $("settings") && settings.close());
for (const b of document.querySelectorAll(".lang button")) b.addEventListener("click", () => setLang(b.dataset.lang));
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (!$("wizard").hidden) wz.close();
  if (!$("settings").hidden) settings.close();
});

(async () => {
  applyStatic();
  try {
    countries = await api("/api/countries");
  } catch (e) {
    $("load-error").textContent = t("serverError", { msg: errText(e) });
    $("load-error").hidden = false;
  }
  await Promise.all([loadFormatLabels(), loadAlerts()]);
  setInterval(loadAlerts, 30000);
})();
