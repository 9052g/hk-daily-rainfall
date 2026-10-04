# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Add monthly mean air temperature inside the separate rainfall curve artwork."""

import csv
import datetime as dt
import math
import runpy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).parent
BASE_IMAGE = HERE / "out" / "rainfall_closed_curve.png"
OUTPUT = HERE / "out" / "rainfall_temperature_ring.png"
INNER, OUTER = 248, 313
CX, CY = 900, 910
GREEN = (40, 149, 110)
YELLOW = (245, 195, 77)
RED = (211, 68, 68)
INK = (23, 43, 58)
MUTED = (100, 118, 134)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = (
        ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
        if bold else
        ["/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise RuntimeError("An Arial or DejaVu Sans font is needed to draw the chart")


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def temperature_colour(celsius: float) -> tuple[int, int, int]:
    """A fixed 15–30 °C scale makes the green/red meaning explicit."""
    position = max(0.0, min(1.0, (celsius - 15) / 15))
    if position <= 0.5:
        return mix(GREEN, YELLOW, position * 2)
    return mix(YELLOW, RED, (position - 0.5) * 2)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[float, float], label: str,
             face: ImageFont.FreeTypeFont, colour: tuple[int, int, int]) -> None:
    box = draw.textbbox((0, 0), label, font=face)
    draw.text((xy[0] - (box[2] - box[0]) / 2,
               xy[1] - (box[3] - box[1]) / 2 - box[1]),
              label, font=face, fill=colour)


def temperature_by_date() -> dict[dt.date, tuple[float, str]]:
    readings = {}
    for year in (2025, 2026):
        path = HERE / "data" / f"daily_HKO_TEMP_{year}.csv"
        with path.open(encoding="utf-8-sig", newline="") as source:
            next(source)
            next(source)
            for row in csv.DictReader(source):
                try:
                    date = dt.date(int(row["年/Year"]), int(row["月/Month"]),
                                   int(row["日/Day"]))
                    value = float(row["數值/Value"])
                    completeness = row["數據完整性/data Completeness"]
                except (KeyError, TypeError, ValueError):
                    continue  # The official CSV ends with explanatory footer lines.
                if date in readings:
                    raise ValueError(f"Duplicate temperature reading: {date}")
                readings[date] = (value, completeness)
    return readings


days = runpy.run_path(str(HERE / "site.py"))["load_recent_days"](
    HERE / "data" / "daily_HKO_RF_ALL.csv")
temperature = temperature_by_date()
missing = [day["date"] for day in days if day["date"] not in temperature]
incomplete = [day["date"] for day in days
              if day["date"] in temperature and temperature[day["date"]][1] != "C"]
if missing or incomplete:
    raise ValueError(f"Temperature coverage problem: {len(missing)} missing, "
                     f"{len(incomplete)} incomplete days")

months = []
for index, day in enumerate(days):
    date = day["date"]
    key = (date.year, date.month)
    if not months or months[-1]["key"] != key:
        months.append({"key": key, "start": index, "end": index, "values": []})
    months[-1]["end"] = index
    months[-1]["values"].append(temperature[date][0])
if len(months) != 12:
    raise ValueError(f"Expected 12 complete months, found {len(months)}")

with Image.open(BASE_IMAGE) as original:
    canvas = original.convert("RGB")
draw = ImageDraw.Draw(canvas)
size = canvas.size
if size != (1800, 1800):
    raise ValueError(f"Unexpected base image size: {size}")

for month in months:
    average = sum(month["values"]) / len(month["values"])
    month["average"] = average
    start = -90 + 360 * month["start"] / len(days)
    end = -90 + 360 * (month["end"] + 1) / len(days)
    draw.pieslice((CX - OUTER, CY - OUTER, CX + OUTER, CY + OUTER),
                  start=start, end=end, fill=temperature_colour(average))

# Cut out the centre, separate the monthly sectors, and write each mean on its arc.
draw.ellipse((CX - INNER, CY - INNER, CX + INNER, CY + INNER), fill="white")
for month in months:
    angle = 2 * math.pi * month["start"] / len(days)
    x0, y0 = CX + math.sin(angle) * INNER, CY - math.cos(angle) * INNER
    x1, y1 = CX + math.sin(angle) * OUTER, CY - math.cos(angle) * OUTER
    draw.line((x0, y0, x1, y1), fill="white", width=3)
    middle = (month["start"] + month["end"]) / 2
    angle = 2 * math.pi * middle / len(days)
    radius = (INNER + OUTER) / 2
    x, y = CX + math.sin(angle) * radius, CY - math.cos(angle) * radius
    colour = INK if 21.5 < month["average"] < 26 else (255, 255, 255)
    centered(draw, (x, y), f"{month['average']:.1f}°", font(19, bold=True), colour)

draw.ellipse((CX - INNER, CY - INNER, CX + INNER, CY + INNER),
             outline=(214, 225, 229), width=2)
centered(draw, (900, 768), "RAIN + TEMP", font(52, bold=True), INK)
centered(draw, (900, 827), "HONG KONG OBSERVATORY", font(22, bold=True), (20, 107, 157))
centered(draw, (900, 886), f"{sum(day['rain'] for day in days):,.0f} mm  ·  365 days",
         font(28), INK)
centered(draw, (900, 936),
         f"{days[0]['date']:%d %b %Y} — {days[-1]['date']:%d %b %Y}",
         font(21), MUTED)
centered(draw, (900, 996), "INNER RING  /  MONTHLY MEAN AIR TEMP", font(17), MUTED)

for x in range(782, 1019):
    colour = temperature_colour(15 + 15 * (x - 782) / (1018 - 782))
    draw.line((x, 1031, x, 1045), fill=colour, width=1)
centered(draw, (782, 1070), "15°C", font(18), GREEN)
centered(draw, (1018, 1070), "30°C", font(18), RED)

draw.rectangle((380, 1605, 1420, 1720), fill="white")
centered(draw, (900, 1646), "Daily rainfall outside  ·  monthly mean air temperature inside",
         font(22), MUTED)
centered(draw, (900, 1690), "Hong Kong Observatory  /  rainfall in mm  ·  air temperature in °C",
         font(18), MUTED)

OUTPUT.parent.mkdir(exist_ok=True)
canvas.save(OUTPUT, optimize=True)
print("Monthly mean temperatures (°C):", ", ".join(
    f"{month['key'][0]}-{month['key'][1]:02d} {month['average']:.1f}"
    for month in months))
print(f"Combined artwork saved to {OUTPUT}")
