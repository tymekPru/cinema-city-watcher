"use strict";

const STEPS = ["Country", "Movie", "Cinema", "Format", "Language", "Dates"];
const LANGUAGE_LABELS = { subbed: "Subtitled", dubbed: "Dubbed", original: "Original" };
const SETTINGS_FIELDS = [
  { section: "api", key: "requestGapSeconds", label: "Request gap (seconds)", step: "0.05", help: "Minimum pause between two requests to the Cinema City API." },
  { section: "api", key: "cacheSeconds", label: "Catalogue cache (seconds)", step: "1", help: "How long film, cinema and format lists are cached for this UI." },
  { section: "alerts", key: "minRatioDelta", label: "Minimum seat change (ratio)", step: "0.001", help: "Rise in free-seat ratio that counts as new seats. One seat in a 385-seat hall is about 0.0026." },
  { section: "alerts", key: "cooldownMinutes", label: "Alert cooldown (minutes)", step: "1", help: "Do not repeat the same alert for the same screening within this time." },
  { section: "runtime", key: "pollIntervalSeconds", label: "Poll interval (seconds)", step: "1", help: "Pause between sweeps when the watcher runs with --keep-alive." },
  { section: "runtime", key: "dataDir", label: "Data directory", type: "text", help: "Where alerts.json and state.json live. Relative to appsettings.json." },
];

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
  if (!res.ok) throw new Error(data.error || `${res.status} ${res.statusText}`);
  return data;
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + (iso.length === 10 ? "T00:00:00" : ""));
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function fmtDateTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function relTime(iso) {
  if (!iso) return "never";
  const s = Math.round((Date.now() - new Date(iso)) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

// ---------- overview table ----------

const formatLabels = {};
let countries = [];
const expanded = new Set();

function splitAttrs(attrs) {
  return {
    format: attrs.find((a) => !(a in LANGUAGE_LABELS)),
    language: attrs.find((a) => a in LANGUAGE_LABELS),
  };
}

const countryName = (code) => (countries.find((c) => c.code === code) || {}).name || code.toUpperCase();
const formatLabel = (id) => (id ? formatLabels[id] || id : "any");
const languageLabel = (id) => (id ? LANGUAGE_LABELS[id] || id : "any");
const anyOr = (value) => (value ? value : el("span", { class: "muted" }, "any"));

function row(a) {
  const { format, language } = splitAttrs(a.attrs);
  const tr = el(
    "tr",
    { class: "row" + (expanded.has(a.id) ? " open" : ""), onclick: () => toggleDetails(a) },
    el("td", {}, a.film.name, el("span", { class: "sub" }, countryName(a.country))),
    el("td", {}, a.cinema.name, a.cinema.imax ? el("span", { class: "tag", style: "margin-left:8px" }, "IMAX") : ""),
    el("td", {}, anyOr(format && formatLabel(format))),
    el("td", {}, anyOr(language && languageLabel(language))),
    el("td", {}, `${fmtDate(a.dateFrom)} – ${fmtDate(a.dateTo)}`),
    el("td", {}, el("span", { class: `pill ${a.status}` }, a.status)),
    el("td", {}, relTime(a.lastSweep), a.lastAlert ? el("span", { class: "sub" }, `alerted ${relTime(a.lastAlert)}`) : ""),
    el("td", { class: "num" }, String(a.tracked)),
    el(
      "td",
      { class: "actions" },
      el("button", { class: "btn danger", onclick: (e) => { e.stopPropagation(); removeAlert(a); } }, "Delete")
    )
  );
  return tr;
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
    el("dt", {}, "Country"), el("dd", {}, countryName(a.country)),
    el("dt", {}, "Film"), el("dd", {}, a.film.name, el("span", { class: "sub" }, a.film.id)),
    el("dt", {}, "Cinema"), el("dd", {}, a.cinema.name + (a.cinema.imax ? " (IMAX)" : ""), el("span", { class: "sub" }, a.cinema.id)),
    el("dt", {}, "Format"), el("dd", {}, formatLabel(format)),
    el("dt", {}, "Language"), el("dd", {}, languageLabel(language)),
    el("dt", {}, "Dates"), el("dd", {}, `${fmtDate(a.dateFrom)} – ${fmtDate(a.dateTo)}`),
    el("dt", {}, "Created"), el("dd", {}, fmtDateTime(a.createdAt)),
    el("dt", {}, "Last check"), el("dd", {}, relTime(a.lastSweep)),
    el("dt", {}, "Id"), el("dd", {}, a.id)
  );
  const shots = el("div", { class: "shots" }, el("p", { class: "muted" }, "Loading…"));
  api(`/api/alerts/${a.id}/events`)
    .then((events) => {
      if (!events.length) {
        shots.replaceChildren(el("p", { class: "muted" }, a.lastSweep ? "No matching screenings on sale right now." : "Not checked yet. Run the watcher once."));
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
            el("span", { class: "pct" }, ev.soldOut ? "sold out" : `${Math.round(fill * 100)}% sold`),
            ev.book ? el("a", { href: ev.book, target: "_blank", rel: "noopener" }, "Book") : ""
          );
        })
      );
    })
    .catch((e) => shots.replaceChildren(el("p", { class: "error" }, e.message)));
  return el(
    "tr",
    { class: "details" },
    el(
      "td",
      { colspan: "9" },
      el(
        "div",
        { class: "detail-grid" },
        el("div", {}, el("h4", {}, "Alert"), props),
        el("div", {}, el("h4", {}, `Tracked screenings (${a.tracked})`), shots)
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
    err.textContent = `Could not load alerts: ${e.message}`;
    err.hidden = false;
  }
}

async function removeAlert(a) {
  if (!confirm(`Delete the alert for "${a.film.name}" at ${a.cinema.name}?`)) return;
  try {
    await api(`/api/alerts/${a.id}`, { method: "DELETE" });
    await loadAlerts();
  } catch (e) {
    alert(`Delete failed: ${e.message}`);
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
    $("st-fields").replaceChildren(el("p", { class: "muted" }, "Loading…"));
    api("/api/settings")
      .then((data) => {
        $("st-fields").replaceChildren(
          ...SETTINGS_FIELDS.map((f) =>
            el(
              "div",
              { class: "field" },
              el("label", { for: `st-${f.section}-${f.key}` }, f.label),
              el("input", {
                id: `st-${f.section}-${f.key}`,
                type: f.type || "number",
                step: f.step,
                min: f.type ? null : "0",
                value: data[f.section][f.key],
              }),
              el("span", { class: "help" }, f.help)
            )
          )
        );
      })
      .catch((e) => this.showError(e.message));
  },
  close() {
    $("settings").hidden = true;
  },
  showError(msg) {
    $("st-error").textContent = msg || "";
    $("st-error").hidden = !msg;
  },
  async save() {
    const patch = {};
    for (const f of SETTINGS_FIELDS) {
      const input = $(`st-${f.section}-${f.key}`);
      if (!input) return;
      const value = f.type === "text" ? input.value : Number(input.value);
      if (f.type !== "text" && !Number.isFinite(value)) return this.showError(`${f.label} must be a number.`);
      (patch[f.section] ||= {})[f.key] = value;
    }
    $("st-save").disabled = true;
    try {
      await api("/api/settings", { method: "PUT", body: JSON.stringify(patch) });
      this.close();
    } catch (e) {
      this.showError(e.message);
    } finally {
      $("st-save").disabled = false;
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
    this.draft = {};
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
    if (this.step === STEPS.length - 1) return this.save();
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
    if (key === "film") {
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
      ...STEPS.map((s, i) => el("li", { class: i < this.step ? "done" : i === this.step ? "current" : "" }, `${i + 1}. ${s}`))
    );
    $("wz-back").disabled = this.step === 0;
    $("wz-next").textContent = this.step === STEPS.length - 1 ? "Save alert" : "Next";
    $("wz-next").disabled = !this.canAdvance();
    const body = $("wz-body");
    body.replaceChildren(el("p", { class: "muted" }, "Loading…"));
    [this.country, this.movie, this.cinema, this.format, this.language, this.dates][this.step]
      .call(this, body)
      .catch((e) => body.replaceChildren(el("p", { class: "error" }, e.message)));
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

  choices(body, title, hint, items, selected, onPick, toolbar) {
    body.replaceChildren(
      el("h3", {}, title),
      el("p", { class: "hint muted" }, hint),
      toolbar || "",
      el("div", { class: "choices" }, ...items.map((it) => this.choiceButton(it, selected === it.value, onPick)))
    );
  },

  async country(body) {
    this.choices(
      body,
      "Which country?",
      "Film catalogues differ per country, so this comes first.",
      countries.map((c) => ({ value: c.code, title: c.name, meta: c.code.toUpperCase() })),
      this.draft.country,
      (it) => this.pick("country", it.value)
    );
  },

  async movie(body) {
    const films = await this.fetch(`/api/${this.draft.country}/films`);
    const search = el("input", { class: "search", type: "search", placeholder: "Search films…" });
    const list = el("div", { class: "choices" });
    const draw = () => {
      const q = search.value.trim().toLowerCase();
      list.replaceChildren(
        ...films
          .filter((f) => !q || f.name.toLowerCase().includes(q))
          .map((f) =>
            this.choiceButton(
              {
                value: f.id,
                img: f.posterLink || null,
                title: f.name,
                meta: [f.releaseDate && `from ${fmtDate(f.releaseDate)}`, f.length && `${f.length} min`, f.attributeIds.filter((a) => a in formatLabels).map(formatLabel).join(", ")]
                  .filter(Boolean)
                  .join(" · "),
                raw: f,
              },
              this.draft.film && this.draft.film.id === f.id,
              (it) => this.pick("film", it.raw)
            )
          )
      );
    };
    search.addEventListener("input", draw);
    body.replaceChildren(el("h3", {}, "Which movie?"), el("p", { class: "hint muted" }, `${films.length} films currently on sale.`), search, list);
    draw();
    search.focus();
  },

  async cinema(body) {
    const cinemas = await this.fetch(`/api/${this.draft.country}/cinemas`);
    const search = el("input", { class: "search", type: "search", placeholder: "Search cinemas…" });
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
      if (!shown.length) list.replaceChildren(el("p", { class: "muted" }, "No cinemas match."));
    };
    search.addEventListener("input", draw);
    imaxOnly.addEventListener("change", draw);
    body.replaceChildren(
      el("h3", {}, "Which cinema?"),
      el("p", { class: "hint muted" }, `${cinemas.length} cinemas, ${cinemas.filter((c) => c.imax).length} with an IMAX screen.`),
      el("div", { class: "toolbar" }, search, el("label", { class: "switch" }, imaxOnly, el("span", { class: "track" }), "IMAX only")),
      list
    );
    draw();
    search.focus();
  },

  async format(body) {
    const formats = await this.fetch(`/api/${this.draft.country}/formats`);
    const onFilm = new Set(this.draft.film.attributeIds);
    const items = [{ value: "", title: "Any format", meta: "Alert on every screening of this film" }].concat(
      [...formats]
        .sort((a, b) => onFilm.has(b.id) - onFilm.has(a.id))
        .map((f) => ({ value: f.id, title: f.label, meta: onFilm.has(f.id) ? "" : "not offered for this film", disabled: !onFilm.has(f.id) }))
    );
    this.choices(body, "Which format?", "One format per alert. Formats this film is not offered in are greyed out.", items, this.draft.format, (it) => this.pick("format", it.value));
  },

  async language(body) {
    const langs = this.draft.film.languages || {};
    const items = [{ value: "", title: "Any language", meta: "" }];
    if ((langs.subtitles || []).length) items.push({ value: "subbed", title: "Subtitled", meta: `original ${(langs.original || []).join(", ") || "audio"}, subtitles ${langs.subtitles.join(", ")}` });
    if ((langs.dubbed || []).length) items.push({ value: "dubbed", title: "Dubbed", meta: langs.dubbed.join(", ") });
    if ((langs.original || []).length && !(langs.subtitles || []).length) items.push({ value: "original", title: "Original", meta: langs.original.join(", ") });
    this.choices(body, "Which language version?", items.length > 1 ? "Based on what this film is offered in." : "No language details for this film.", items, this.draft.language, (it) => this.pick("language", it.value));
  },

  async dates(body) {
    const today = new Date().toISOString().slice(0, 10);
    const release = this.draft.film.releaseDate || today;
    const from = this.draft.dateFrom || (release > today ? release : today);
    const plus = new Date(from + "T00:00:00");
    plus.setDate(plus.getDate() + 60);
    const to = this.draft.dateTo || plus.toISOString().slice(0, 10);
    const inFrom = el("input", { type: "date", value: from, min: today, oninput: () => (this.draft.dateFrom = inFrom.value) });
    const inTo = el("input", { type: "date", value: to, min: today, oninput: () => (this.draft.dateTo = inTo.value) });
    this.draft.dateFrom = from;
    this.draft.dateTo = to;
    const d = this.draft;
    body.replaceChildren(
      el("h3", {}, "Which dates?"),
      el("p", { class: "hint muted" }, "Only screenings between these days are watched. Both are required."),
      el("div", { class: "fields" }, el("div", { class: "field" }, el("label", {}, "From"), inFrom), el("div", { class: "field" }, el("label", {}, "To"), inTo)),
      el(
        "div",
        { class: "summary" },
        el("div", {}, el("span", {}, "Film"), el("span", {}, d.film.name)),
        el("div", {}, el("span", {}, "Cinema"), el("span", {}, d.cinema.name + (d.cinema.imax ? " (IMAX)" : ""))),
        el("div", {}, el("span", {}, "Format"), el("span", {}, formatLabel(d.format))),
        el("div", {}, el("span", {}, "Language"), el("span", {}, languageLabel(d.language)))
      )
    );
  },

  async save() {
    const d = this.draft;
    if (!d.dateFrom || !d.dateTo) return this.showError("Both dates are required.");
    if (d.dateFrom > d.dateTo) return this.showError("The start date must not be after the end date.");
    const payload = {
      country: d.country,
      film: { id: d.film.id, name: d.film.name },
      cinema: { id: d.cinema.id, name: d.cinema.name, imax: d.cinema.imax },
      attrs: [d.format, d.language].filter(Boolean),
      dateFrom: d.dateFrom,
      dateTo: d.dateTo,
    };
    $("wz-next").disabled = true;
    try {
      await api("/api/alerts", { method: "POST", body: JSON.stringify(payload) });
      this.close();
      await loadAlerts();
    } catch (e) {
      this.showError(e.message);
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
$("settings").addEventListener("click", (e) => e.target === $("settings") && settings.close());
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (!$("wizard").hidden) wz.close();
  if (!$("settings").hidden) settings.close();
});

(async () => {
  try {
    countries = await api("/api/countries");
  } catch (e) {
    $("load-error").textContent = `Could not reach the server: ${e.message}`;
    $("load-error").hidden = false;
  }
  await Promise.all([loadFormatLabels(), loadAlerts()]);
  setInterval(loadAlerts, 30000);
})();
