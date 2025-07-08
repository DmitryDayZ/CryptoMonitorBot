import os

import pandas as pd
import zipfile
from pathlib import Path
from datetime import datetime

HISTORICAL_DIR = "/historydata"
EXTRACTED_DIR = "/tmp"  # временный каталог
# Имена столбцов из CSV
BINANCE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"
]
def get_all_zip_files() -> list[str]:
    return sorted([
        f for f in os.listdir(HISTORICAL_DIR)
        if f.endswith(".zip") and not f.endswith(".CHECKSUM")
    ])

def unzip_to_dataframe(zip_path: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(EXTRACTED_DIR)
    # Предполагаем, что внутри один .csv
    csv_files = [f for f in os.listdir(EXTRACTED_DIR) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError("Нет .csv в архиве")
    csv_path = os.path.join(EXTRACTED_DIR, csv_files[0])
    df = pd.read_csv(csv_path, header=None)
    df.columns = ["timestamp", "open", "high", "low", "close", "volume"]  # если без заголовков
    return df


def load_all_data_to_dataframe(data_dir: str = "data", start_date: datetime = None,
                               end_date: datetime = None) -> pd.DataFrame:
    all_data = []

    for zip_path in Path(data_dir).glob("*.zip"):
        with zipfile.ZipFile(zip_path) as z:
            for csv_filename in z.namelist():
                with z.open(csv_filename) as f:
                    df = pd.read_csv(f, header=None, names=BINANCE_COLUMNS, skiprows=1)
                    df["datetime"] = pd.to_datetime(df["open_time"], unit="ms")
                    all_data.append(df)

    if not all_data:
        return pd.DataFrame()

    result = pd.concat(all_data, ignore_index=True)

    # Фильтрация по дате
    if start_date:
        result = result[result["datetime"] >= start_date]
    if end_date:
        result = result[result["datetime"] <= end_date]

    return result.sort_values("datetime").reset_index(drop=True)