# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pandas", "numpy"]
# ///

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize


INK = "#172b3a"
MUTED = "#647686"
BACKGROUND = "#ffffff"
RING = "#d6e2e9"
RAIN_COLOURS = ["#91cdeb", "#4f9ecb", "#1d6fa5", "#0d4b81", "#082e5a"]


def load_rainfall_csv(file_path: Path) -> pd.DataFrame:
    """Read the committed HKO file and return the latest 365 calendar days."""
    df = pd.read_csv(file_path, skiprows=2)
    date_parts = {name: pd.to_numeric(df[column], errors="coerce") for name, column in {
        "year": "年/Year", "month": "月/Month", "day": "日/Day"
    }.items()}
    df["date"] = pd.to_datetime(date_parts, errors="coerce")
    raw_rain = df["數值/Value"].astype(str).str.strip()
    df["rainfall"] = pd.to_numeric(raw_rain, errors="coerce")
    # HKO defines “Trace” as less than 0.05 mm; retain it as a visible 0.025 mm.
    trace_mask = raw_rain.str.contains("Trace|微量", case=False, regex=True)
    df.loc[trace_mask, "rainfall"] = 0.025
    df = df.dropna(subset=["date", "rainfall"])
    latest = df["date"].max()
    first = latest - pd.Timedelta(days=364)
    return df[df["date"].between(first, latest)].reset_index(drop=True)


def month_positions(dates: pd.Series) -> list[tuple[float, str]]:
    """Return the angular midpoint and short label for each month in the data."""
    positions = []
    for (_, month), group in dates.groupby([dates.dt.year, dates.dt.month]):
        middle_index = (group.index[0] + group.index[-1]) / 2
        angle = 2 * np.pi * middle_index / len(dates)
        positions.append((angle, group.iloc[0].strftime("%b")))
    return positions


def plot_rainfall_wheel(df: pd.DataFrame, output_image: Path) -> None:
    """Turn one year of daily rainfall into a circular field of rain marks."""
    days = len(df)
    angles = np.linspace(0, 2 * np.pi, days, endpoint=False)
    rain = df["rainfall"].to_numpy()
    visual_rain = np.sqrt(rain)
    maximum = visual_rain.max() or 1
    lengths = 0.25 + 2.55 * visual_rain / maximum
    baseline = 3.05
    width = (2 * np.pi / days) * 0.72

    cmap = LinearSegmentedColormap.from_list("rain", RAIN_COLOURS)
    norm = Normalize(vmin=0, vmax=maximum)

    fig = plt.figure(figsize=(10, 10), dpi=220, facecolor=BACKGROUND)
    ax = fig.add_subplot(111, projection="polar", facecolor=BACKGROUND)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Every day gets a faint mark; wet days bloom outwards in colour.
    for angle, amount, length in zip(angles, rain, lengths):
        if amount <= 0:
            ax.bar(angle, 0.10, width=width * 0.42, bottom=baseline,
                   color=RING, alpha=0.85, linewidth=0)
        else:
            colour = cmap(norm(np.sqrt(amount)))
            ax.bar(angle, length, width=width, bottom=baseline,
                   color=colour, alpha=0.92, linewidth=0)
            ax.scatter(angle, baseline + length, s=7 + min(amount, 80) * 0.24,
                       color=colour, alpha=0.92, edgecolors="none", zorder=4)

    # Fine circular guides make magnitude readable without dominating the image.
    for value in (10, 50, 100):
        radius = baseline + 0.25 + 2.55 * np.sqrt(value) / maximum
        if radius <= baseline + 2.9:
            theta = np.linspace(0, 2 * np.pi, 500)
            ax.plot(theta, np.full_like(theta, radius), color=RING,
                    linewidth=0.55, alpha=0.85, zorder=0)
            ax.text(np.deg2rad(357), radius, f" {value} mm", color=MUTED,
                    fontsize=6.5, ha="left", va="center")

    for angle, label in month_positions(df["date"]):
        ax.text(angle, baseline - 0.20, label.upper(), color=MUTED, fontsize=7.5,
                ha="center", va="center")

    total = rain.sum()
    wet_days = int((rain > 0).sum())
    start = df["date"].iloc[0].strftime("%d %b %Y")
    end = df["date"].iloc[-1].strftime("%d %b %Y")
    ax.text(0.5, 0.535, "RAIN / YEAR", transform=ax.transAxes, color=INK,
            fontsize=23, fontweight="bold", ha="center", va="center")
    ax.text(0.5, 0.492, "HONG KONG OBSERVATORY", transform=ax.transAxes,
            color="#087b91", fontsize=9, fontweight="bold", ha="center")
    ax.text(0.5, 0.452, f"{total:,.0f} mm  ·  {wet_days} rain/trace days",
            transform=ax.transAxes, color=INK, fontsize=10, ha="center")
    ax.text(0.5, 0.421, f"{start} — {end}", transform=ax.transAxes,
            color=MUTED, fontsize=7.5, ha="center")
    ax.text(0.5, 0.055, "Each mark is one day · longer, darker blue means more rain",
            transform=ax.transAxes, color=MUTED, fontsize=7.5, ha="center")

    ax.set_ylim(0, baseline + 3.15)
    ax.set_axis_off()
    fig.savefig(output_image, facecolor=BACKGROUND, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)
    print(f"Rainfall wheel saved to {output_image}")


if __name__ == "__main__":
    output_folder = Path("out")
    output_folder.mkdir(exist_ok=True)
    rainfall = load_rainfall_csv(Path("data/daily_HKO_RF_ALL.csv"))
    plot_rainfall_wheel(rainfall, output_folder / "rainfall_chart.png")
