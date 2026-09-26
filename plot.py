# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pandas"]
# ///
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates

# 全局样式：极简干净
plt.rcParams["font.family"] = ["Arial"]
plt.rcParams["axes.spines.top"] = False    # 隐藏顶部边框
plt.rcParams["axes.spines.right"] = False # 隐藏右侧边框
plt.rcParams["axes.edgecolor"] = "#444444"
plt.rcParams["axes.linewidth"] = 0.7

def load_rainfall_csv(file_path: Path) -> pd.DataFrame:
    df = pd.read_csv(file_path, skiprows=2)

    df["年/Year"] = pd.to_numeric(df["年/Year"], errors="coerce")
    df["月/Month"] = pd.to_numeric(df["月/Month"], errors="coerce")
    df["日/Day"] = pd.to_numeric(df["日/Day"], errors="coerce")

    df = df.dropna(subset=["年/Year", "月/Month", "日/Day"])

    df["full_date"] = pd.to_datetime(
        {
            "year": df["年/Year"],
            "month": df["月/Month"],
            "day": df["日/Day"],
        },
        errors="coerce"
    )
    df = df.dropna(subset=["full_date"])
    return df

def plot_rainfall_chart(df: pd.DataFrame, output_image: Path):
    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)

    # 折线 + 下方淡蓝色填充，氛围感更强
    ax.plot(df["full_date"], df["數值/Value"], color="#2E86AB", linewidth=1.3)
    ax.fill_between(df["full_date"], df["數值/Value"], color="#A23B72", alpha=0.12)

    ax.set_title("Daily Rainfall at Hong Kong Observatory (Latest 365 Days)", fontsize=13, pad=14, weight="medium")
    ax.set_xlabel("Date", fontsize=11, labelpad=8)
    ax.set_ylabel("Daily Rainfall (mm)", fontsize=11, labelpad=8)

    # X轴：2个月一个标记
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    # Y轴：最多6个刻度，防止重叠
    ax.yaxis.set_major_locator(plt.MaxNLocator(6))

    # 只保留横向网格线，竖线删掉，更干净
    ax.grid(axis="y", alpha=0.2, linestyle="-")

    plt.xticks(rotation=30, fontsize=9)
    plt.yticks(fontsize=9)

    fig.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Art style chart saved to {output_image}")

if __name__ == "__main__":
    data_file = Path("data/daily_HKO_RF_ALL.csv")
    out_folder = Path("out")
    out_folder.mkdir(exist_ok=True)
    df_data = load_rainfall_csv(data_file)
    df_recent = df_data.tail(365)
    plot_rainfall_chart(df_recent, out_folder / "rainfall_chart.png")
