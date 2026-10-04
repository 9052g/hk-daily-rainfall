# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Render a separate, closed line-only interpretation of the rainfall year."""

import math
import runpy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUTPUT = HERE / "out" / "rainfall_closed_curve.png"
load_recent_days = runpy.run_path(str(HERE / "site.py"))["load_recent_days"]
days = load_recent_days(HERE / "data" / "daily_HKO_RF_ALL.csv")
rain = [day["rain"] for day in days]

SIZE = 1800
CX, CY = 900, 910
BASE = 382
LENGTH = 310
INK = (23, 43, 58)
MUTED = (100, 118, 134)
GUIDE = (226, 237, 244)


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


def point(day_position: float, radius: float) -> tuple[float, float]:
    angle = day_position * 2 * math.pi / len(days)
    return CX + math.sin(angle) * radius, CY - math.cos(angle) * radius


def centered(draw: ImageDraw.ImageDraw, location: tuple[float, float], label: str,
             face: ImageFont.FreeTypeFont, color: tuple[int, int, int]) -> None:
    box = draw.textbbox((0, 0), label, font=face)
    draw.text((location[0] - (box[2] - box[0]) / 2,
               location[1] - (box[3] - box[1]) / 2 - box[1]),
              label, font=face, fill=color)


def gaussian_average(values: list[float], sigma: float = 1.5) -> list[float]:
    """Lightly smooth the circular trace without changing the source data."""
    reach = math.ceil(3 * sigma)
    result = []
    for index in range(len(values)):
        numerator = denominator = 0.0
        for shift in range(-reach, reach + 1):
            neighbor = (index + shift) % len(values)
            weight = math.exp(-0.5 * (shift / sigma) ** 2)
            numerator += values[neighbor] * weight
            denominator += weight
        result.append(numerator / denominator)
    return result


averages = gaussian_average(rain)
largest = max(averages)
radii = [BASE + 12 + LENGTH * math.sqrt(amount / largest) for amount in averages]
slopes = [(radii[(index + 1) % len(radii)] - radii[(index - 1) % len(radii)]) / 2
          for index in range(len(radii))]

canvas = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
draw = ImageDraw.Draw(canvas)

for amount in (5, 20, 50):
    if amount >= largest:
        continue
    radius = BASE + 12 + LENGTH * math.sqrt(amount / largest)
    draw.ellipse((CX - radius, CY - radius, CX + radius, CY + radius),
                 outline=GUIDE, width=2)
    x, y = point(364.2, radius)
    draw.text((x + 7, y), f"{amount} mm", font=font(16), fill=MUTED, anchor="lm")

draw.ellipse((CX - BASE, CY - BASE, CX + BASE, CY + BASE),
             outline=(201, 222, 235), width=3)

previous = point(0, radii[0])
for index in range(len(radii)):
    next_index = (index + 1) % len(radii)
    for step in range(1, 11):
        t = step / 10
        t2, t3 = t * t, t * t * t
        radius = ((2 * t3 - 3 * t2 + 1) * radii[index]
                  + (t3 - 2 * t2 + t) * slopes[index]
                  + (-2 * t3 + 3 * t2) * radii[next_index]
                  + (t3 - t2) * slopes[next_index])
        current = point(index + t, radius)
        strength = max(0.0, min(1.0, (radius - BASE - 12) / LENGTH))
        colour = mix((98, 173, 213), (9, 61, 121), strength ** 0.9)
        draw.line((previous, current), fill=colour, width=5)
        previous = current

first = 0
while first < len(days):
    year, month = days[first]["date"].year, days[first]["date"].month
    last = first
    while (last + 1 < len(days)
           and days[last + 1]["date"].year == year
           and days[last + 1]["date"].month == month):
        last += 1
    x, y = point((first + last) / 2, BASE - 38)
    centered(draw, (x, y), days[first]["date"].strftime("%b").upper(), font(19), MUTED)
    first = last + 1

centered(draw, (900, 790), "RAIN / YEAR", font(54, bold=True), INK)
centered(draw, (900, 855), "ONE CONTINUOUS YEAR", font(25, bold=True), (20, 107, 157))
centered(draw, (900, 914), f"{sum(rain):,.0f} mm  ·  365 days", font(28), INK)
centered(draw, (900, 966),
         f"{days[0]['date']:%d %b %Y} — {days[-1]['date']:%d %b %Y}",
         font(21), MUTED)
centered(draw, (900, 1646), "Line only  ·  lightly smoothed rainfall  ·  closed annual cycle",
         font(22), MUTED)
centered(draw, (900, 1690), "Hong Kong Observatory  /  rainfall in millimetres", font(18), MUTED)

OUTPUT.parent.mkdir(exist_ok=True)
canvas.save(OUTPUT, optimize=True)
print(f"Closed rainfall curve saved to {OUTPUT}")
