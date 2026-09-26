# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
import requests
from pathlib import Path

def fetch_hko_daily_rainfall(save_path: Path):
    # HKO 香港天文台 每日雨量CSV
    url = "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/ALL/daily_HKO_RF_ALL.csv"
    resp = requests.get(url)
    resp.raise_for_status()
    # 原样保存原始CSV，不修改原始内容
    save_path.write_bytes(resp.content)
    print(f"Raw rainfall CSV saved to {save_path}")

if __name__ == "__main__":
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / "daily_HKO_RF_ALL.csv"
    fetch_hko_daily_rainfall(out_file)
