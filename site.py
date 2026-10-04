# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Build a self-contained interactive rainfall page from the committed CSV."""

import argparse
import calendar
import csv
import datetime as dt
import json
from pathlib import Path


HERE = Path(__file__).parent
DATA = HERE / "data" / "daily_HKO_RF_ALL.csv"
OUTPUT = HERE / "site" / "index.html"


def load_recent_days(path: Path) -> list[dict]:
    """Return the latest 365 calendar days, including HKO's trace readings."""
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as source:
        next(source)
        next(source)
        for row in csv.DictReader(source):
            try:
                day = dt.date(
                    int(row["年/Year"]),
                    int(row["月/Month"]),
                    int(row["日/Day"]),
                )
                raw = row["數值/Value"].strip()
                rain = 0.025 if raw.lower() == "trace" else float(raw)
            except (KeyError, TypeError, ValueError):
                continue  # The HKO file ends with explanatory footer lines.
            rows.append({"date": day, "rain": rain})

    end = max(row["date"] for row in rows)
    start = end - dt.timedelta(days=364)
    recent = [row for row in rows if start <= row["date"] <= end]
    if len(recent) != 365 or len({row["date"] for row in recent}) != 365:
        raise ValueError("The committed file does not contain 365 consecutive days")
    return recent


def page_data(days: list[dict]) -> dict:
    """Give each day a month index and prepare the labels shown on hover."""
    months = []
    month_lookup = {}
    points = []
    for day in days:
        date = day["date"]
        key = (date.year, date.month)
        if key not in month_lookup:
            month_lookup[key] = len(months)
            months.append({
                "name": calendar.month_name[date.month],
                "short": calendar.month_abbr[date.month].upper(),
                "year": date.year,
                "start": len(points),
                "end": len(points),
                "total": 0,
                "rainDays": 0,
            })
        month = months[month_lookup[key]]
        month["end"] = len(points)
        month["total"] += day["rain"]
        month["rainDays"] += day["rain"] > 0
        points.append({
            "date": date.isoformat(),
            "rain": day["rain"],
            "month": month_lookup[key],
        })
    for month in months:
        month["total"] = round(month["total"], 1)
    return {
        "days": points,
        "months": months,
        "total": round(sum(day["rain"] for day in days)),
        "start": days[0]["date"].strftime("%d %b %Y"),
        "end": days[-1]["date"].strftime("%d %b %Y"),
        "maxRain": max(day["rain"] for day in days),
    }


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#ffffff">
  <title>Rain / Year — Hong Kong Observatory</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17314b;
      --muted: #62788d;
      --line: #dbe9f2;
      --blue: #176fa4;
      --paper: #fff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                   "Segoe UI", sans-serif;
    }
    .page {
      max-width: 1360px;
      margin: auto;
      padding: clamp(24px, 4vw, 58px) clamp(20px, 4vw, 60px) 36px;
    }
    .masthead {
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 20px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 20px;
    }
    .eyebrow, .edition {
      margin: 0;
      color: var(--blue);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .19em;
      text-transform: uppercase;
    }
    .edition { color: var(--muted); text-align: right; }
    h1 {
      max-width: 790px;
      margin: 28px 0 8px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(38px, 5.4vw, 74px);
      font-weight: 400;
      line-height: 1.02;
      letter-spacing: -.045em;
    }
    .intro {
      max-width: 700px;
      margin: 14px 0 0;
      color: var(--muted);
      font-size: clamp(14px, 1.35vw, 17px);
      line-height: 1.55;
    }
    .stage {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 240px;
      align-items: center;
      gap: clamp(12px, 3vw, 44px);
      margin: 8px auto 10px;
    }
    .wheel-wrap { min-width: 0; position: relative; }
    #wheel { display: block; width: 100%; height: auto; overflow: visible; }
    .guide { fill: none; stroke: var(--line); stroke-width: 1.25; }
    .baseline { fill: none; stroke: #b7d4e6; stroke-width: 1.7; }
    .month-label {
      fill: var(--muted);
      font-size: 15px;
      font-weight: 700;
      letter-spacing: .13em;
      text-anchor: middle;
      dominant-baseline: middle;
      pointer-events: none;
      transition: fill 180ms, font-size 180ms;
    }
    .month-label.active { fill: #0b4b79; font-size: 17px; }
    .rain-bar {
      fill: none;
      stroke-width: 3.5;
      stroke-linecap: round;
      stroke-dasharray: 1;
      stroke-dashoffset: 1;
      opacity: 0;
      pointer-events: none;
      transition: stroke-dashoffset 580ms cubic-bezier(.16, 1, .3, 1),
                  opacity 140ms ease;
    }
    .rain-bar.active {
      stroke-dashoffset: 0;
      opacity: 1;
      transition-delay: var(--delay);
    }
    .hit-sector { fill: transparent; cursor: pointer; }
    .hit-sector:focus-visible { fill: #1472aa12; outline: none; }
    .center-copy { text-anchor: middle; pointer-events: none; }
    .center-kicker {
      fill: var(--blue);
      font-size: 15px;
      font-weight: 700;
      letter-spacing: .2em;
      text-transform: uppercase;
    }
    .center-main {
      fill: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 52px;
      letter-spacing: -.04em;
    }
    .center-sub { fill: var(--muted); font-size: 15px; }
    .side { align-self: center; }
    .side-rule { width: 42px; height: 2px; background: var(--blue); margin-bottom: 20px; }
    .side h2 {
      margin: 0 0 12px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(23px, 2.5vw, 32px);
      line-height: 1.13;
      font-weight: 400;
    }
    .side p { margin: 0 0 24px; color: var(--muted); line-height: 1.55; font-size: 14px; }
    .side .number { display: block; font-size: 32px; font-weight: 300; letter-spacing: -.05em; }
    .side .unit { color: var(--muted); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }
    .month-list {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 7px;
      margin: 0 auto 25px;
      max-width: 900px;
    }
    .month-button {
      border: 1px solid #cfdfeb;
      border-radius: 100px;
      background: white;
      color: #48677e;
      min-width: 64px;
      padding: 7px 10px;
      cursor: pointer;
      font-family: inherit;
      font-size: 11px;
      font-weight: 700;
      line-height: 1.2;
      letter-spacing: .09em;
    }
    .month-button:hover, .month-button:focus-visible, .month-button[aria-pressed="true"] {
      background: #e7f3fa;
      border-color: #8abdda;
      color: #0b4b79;
      outline: none;
    }
    .all-button { min-width: 100px; border-color: #8abdda; color: #0b4b79; }
    .footer {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 12px;
      border-top: 1px solid var(--line);
      padding-top: 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .footer p { margin: 0; }
    .footer a { color: #165f8e; text-underline-offset: 2px; }
    @media (max-width: 760px) {
      .stage { display: block; margin-top: 12px; }
      .side { margin: -8px auto 22px; max-width: 420px; text-align: center; }
      .side-rule { margin: 0 auto 14px; }
      .side h2 { margin-bottom: 8px; }
      .side p { margin-bottom: 9px; }
      .side .number { font-size: 25px; }
      .month-label { font-size: 17px; }
      .center-main { font-size: 54px; }
    }
    @media (prefers-reduced-motion: reduce) {
      .rain-bar, .month-label { transition-duration: 0ms; transition-delay: 0ms !important; }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <p class="eyebrow">Hong Kong Observatory / daily rainfall</p>
      <p class="edition" id="period"></p>
    </header>
    <h1>A year of rain, revealed month by month.</h1>
    <p class="intro">Move your cursor around the circle. A month’s straight rain marks rise from the inner ring: longer marks and deeper blue tips mean more rainfall. Select a month or reveal the whole year.</p>
    <section class="stage" aria-label="Interactive rainfall wheel">
      <div class="wheel-wrap">
        <svg id="wheel" viewBox="0 0 1000 1000" role="img" aria-label="365-day circular rainfall chart. Hover or select a month, or show every month, to reveal straight daily marks."></svg>
      </div>
      <aside class="side" aria-live="polite">
        <div class="side-rule"></div>
        <h2 id="side-title">Choose a month</h2>
        <p id="side-copy">Hover around the ring or use the month buttons below.</p>
        <span class="number" id="side-number">—</span>
        <span class="unit" id="side-unit">daily rainfall · millimetres</span>
      </aside>
    </section>
    <nav class="month-list" id="month-buttons" aria-label="Choose a month or show the whole year"></nav>
    <footer class="footer">
      <p>One mark per day · 365 days · a square-root length scale keeps heavy storms in view.</p>
      <p><a href="https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/ALL/daily_HKO_RF_ALL.csv">Source: Hong Kong Observatory</a> · “Trace” is shown as 0.025 mm.</p>
    </footer>
  </main>
  <script>
    const data = __DATA__;
    const svg = document.getElementById("wheel");
    const NS = "http://www.w3.org/2000/svg";
    const CX = 500, CY = 500, BASE = 282, MAX_LENGTH = 170;
    const TWO_PI = Math.PI * 2;
    const barsByMonth = data.months.map(() => []);
    const labels = [];
    const buttons = [];
    let allButton;
    const maxRoot = Math.sqrt(data.maxRain);
    let pinned = null;
    let visible = null;

    document.getElementById("period").textContent = data.start + " — " + data.end;

    function add(parent, tag, attributes = {}) {
      const element = document.createElementNS(NS, tag);
      for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
      parent.appendChild(element);
      return element;
    }
    function point(angle, radius) {
      return [CX + Math.sin(angle) * radius, CY - Math.cos(angle) * radius];
    }
    function blue(amount) {
      if (amount === 0) return "#c7dfef";
      const t = Math.sqrt(amount) / maxRoot;
      const stops = [[139, 203, 232], [59, 145, 195], [15, 94, 154], [8, 50, 103]];
      const scaled = t * (stops.length - 1);
      const i = Math.min(Math.floor(scaled), stops.length - 2);
      const fraction = scaled - i;
      const rgb = stops[i].map((value, j) =>
        Math.round(value + (stops[i + 1][j] - value) * fraction));
      return "rgb(" + rgb.join(",") + ")";
    }
    function sector(start, end) {
      const inner = 216, outer = 466;
      const a = point(start, inner), b = point(start, outer);
      const c = point(end, outer), d = point(end, inner);
      const large = end - start > Math.PI ? 1 : 0;
      return "M " + a.join(" ") + " L " + b.join(" ") +
        " A " + outer + " " + outer + " 0 " + large + " 1 " + c.join(" ") +
        " L " + d.join(" ") +
        " A " + inner + " " + inner + " 0 " + large + " 0 " + a.join(" ") + " Z";
    }
    function show(index) {
      buttons.forEach((button, i) => button.setAttribute("aria-pressed", String(i === pinned)));
      allButton.setAttribute("aria-pressed", String(pinned === "all"));
      if (visible === index) return;
      if (visible !== null) {
        if (visible === "all") {
          barsByMonth.flat().forEach(bar => bar.classList.remove("active"));
          labels.forEach(label => label.classList.remove("active"));
        } else {
          barsByMonth[visible].forEach(bar => bar.classList.remove("active"));
          labels[visible].classList.remove("active");
        }
      }
      visible = index;
      if (index === null) {
        document.getElementById("center-main").textContent = "A YEAR";
        document.getElementById("center-sub").textContent = "hover a month to reveal its rain";
        document.getElementById("side-title").textContent = "Choose a month";
        document.getElementById("side-copy").textContent = "Hover around the ring or use the month buttons below.";
        document.getElementById("side-number").textContent = "—";
        document.getElementById("side-unit").textContent = "daily rainfall · millimetres";
        return;
      }
      if (index === "all") {
        barsByMonth.flat().forEach(bar => bar.classList.add("active"));
        labels.forEach(label => label.classList.add("active"));
        document.getElementById("center-main").textContent = "A YEAR";
        document.getElementById("center-sub").textContent = "365 days · all months visible";
        document.getElementById("side-title").textContent = "The whole year";
        document.getElementById("side-copy").textContent = "Each straight mark is one day. Its length shows rainfall; blue deepens from the root to the tip and with the amount.";
        document.getElementById("side-number").textContent = data.total.toLocaleString() + " mm";
        document.getElementById("side-unit").textContent = "annual rainfall";
        return;
      }
      const month = data.months[index];
      barsByMonth[index].forEach(bar => bar.classList.add("active"));
      labels[index].classList.add("active");
      document.getElementById("center-main").textContent = month.short;
      document.getElementById("center-sub").textContent = month.year + " · " + month.rainDays + " rain / trace days";
      document.getElementById("side-title").textContent = month.name + " " + month.year;
      document.getElementById("side-copy").textContent = "Each straight mark is one calendar day. Its length and darker blue tip both follow rainfall.";
      document.getElementById("side-number").textContent = month.total.toLocaleString() + " mm";
      document.getElementById("side-unit").textContent = "monthly rainfall";
    }
    function preview(index) {
      if (pinned === "all" && index !== "all") return;
      show(index);
    }
    function restore() { show(pinned); }
    function toggle(index) {
      pinned = pinned === index ? null : index;
      show(pinned);
    }

    const gradients = add(svg, "defs");
    [BASE, BASE + 56, BASE + 112, BASE + 170].forEach(radius =>
      add(svg, "circle", {cx: CX, cy: CY, r: radius, class: radius === BASE ? "baseline" : "guide"}));

    const bars = add(svg, "g", {"aria-hidden": "true"});
    data.days.forEach((day, index) => {
      const angle = index / data.days.length * TWO_PI;
      const height = Math.sqrt(day.rain) / maxRoot;
      const length = day.rain === 0 ? 9 : 14 + MAX_LENGTH * height;
      const [x1, y1] = point(angle, BASE);
      const [x2, y2] = point(angle, BASE + length);
      const gradientId = "rain-gradient-" + index;
      if (day.rain > 0) {
        const gradient = add(gradients, "linearGradient", {
          id: gradientId, gradientUnits: "userSpaceOnUse",
          x1, y1, x2, y2
        });
        add(gradient, "stop", {offset: "0%", "stop-color": "#b6daed"});
        add(gradient, "stop", {offset: "100%", "stop-color": blue(day.rain)});
      }
      const rank = index - data.months[day.month].start;
      const line = add(bars, "path", {
        d: `M ${x1} ${y1} L ${x2} ${y2}`,
        pathLength: 1, class: "rain-bar",
        stroke: day.rain === 0 ? "#c7dfef" : `url(#${gradientId})`,
        "stroke-width": day.rain === 0 ? 2.2 : 3.5,
        style: "--delay:" + rank * 12 + "ms"
      });
      barsByMonth[day.month].push(line);
    });

    add(svg, "text", {x: CX, y: CY - 64, class: "center-copy center-kicker"})
      .textContent = "RAIN / YEAR";
    add(svg, "text", {x: CX, y: CY + 10, class: "center-copy center-main", id: "center-main"})
      .textContent = "A YEAR";
    add(svg, "text", {x: CX, y: CY + 45, class: "center-copy center-sub", id: "center-sub"})
      .textContent = "hover a month to reveal its rain";
    add(svg, "text", {x: CX, y: CY + 82, class: "center-copy center-sub"})
      .textContent = data.total.toLocaleString() + " mm across 365 days";

    const labelGroup = add(svg, "g");
    data.months.forEach((month, index) => {
      const angle = ((month.start + month.end + 1) / 2) / data.days.length * TWO_PI;
      const [x, y] = point(angle, 245);
      const label = add(labelGroup, "text", {x, y, class: "month-label"});
      label.textContent = month.short;
      labels.push(label);
    });

    const hitGroup = add(svg, "g");
    data.months.forEach((month, index) => {
      const start = month.start / data.days.length * TWO_PI;
      const end = (month.end + 1) / data.days.length * TWO_PI;
      const hit = add(hitGroup, "path", {
        d: sector(start, end), class: "hit-sector", tabindex: "0",
        role: "button", "aria-label": month.name + " " + month.year + ", reveal rainfall"
      });
      hit.addEventListener("pointerenter", event => {
        if (event.pointerType === "mouse") preview(index);
      });
      hit.addEventListener("pointerleave", event => {
        if (event.pointerType === "mouse") restore();
      });
      hit.addEventListener("focus", () => preview(index));
      hit.addEventListener("blur", restore);
      hit.addEventListener("click", () => toggle(index));
      hit.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggle(index);
        }
      });
    });

    const buttonList = document.getElementById("month-buttons");
    allButton = document.createElement("button");
    allButton.type = "button";
    allButton.className = "month-button all-button";
    allButton.textContent = "SHOW ALL";
    allButton.setAttribute("aria-label", "Show all months");
    allButton.setAttribute("aria-pressed", "false");
    allButton.addEventListener("mouseenter", () => preview("all"));
    allButton.addEventListener("mouseleave", restore);
    allButton.addEventListener("focus", () => preview("all"));
    allButton.addEventListener("blur", restore);
    allButton.addEventListener("click", () => toggle("all"));
    buttonList.appendChild(allButton);
    data.months.forEach((month, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "month-button";
      button.textContent = month.short;
      button.setAttribute("aria-label", month.name + " " + month.year);
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("mouseenter", () => preview(index));
      button.addEventListener("mouseleave", restore);
      button.addEventListener("focus", () => preview(index));
      button.addEventListener("blur", restore);
      button.addEventListener("click", () => toggle(index));
      buttonList.appendChild(button);
      buttons.push(button);
    });
  </script>
</body>
</html>
"""


def main(output: Path = OUTPUT) -> None:
    data = page_data(load_recent_days(DATA))
    output.parent.mkdir(exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    output.write_text(HTML.replace("__DATA__", serialized), encoding="utf-8")
    print(f"Interactive rainfall page saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    main(parser.parse_args().output)
